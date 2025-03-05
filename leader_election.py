#!/usr/bin/env python3

import os
import sys
import uuid
import time
import json
import socket
import argparse
import datetime
import threading
from azure.storage.blob import BlobServiceClient, BlobLeaseClient, BlobClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

class LeaderElection:
    def __init__(self, storage_account_name, storage_account_key, container_name, 
                 blob_name="leader", lease_duration=60, node_id=None):
        
        self.storage_account_name = storage_account_name
        self.storage_account_key = storage_account_key
        self.container_name = container_name
        self.blob_name = blob_name
        self.lease_duration = lease_duration
        self.node_id = node_id or f"{socket.gethostname()}-{uuid.uuid4()}"
        self.lease_id = None
        self.is_leader = False
        self.running = False
        self.heartbeat_thread = None
        
        # Conexión a Azure Blob Storage
        connection_string = f"DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey={storage_account_key};EndpointSuffix=core.windows.net"
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)
        self.blob_client = self.container_client.get_blob_client(blob_name)
        
        self._ensure_blob_exists()
    
    def _ensure_blob_exists(self):
        try:
            # Verificar si el blob existe
            try:
                self.blob_client.get_blob_properties()
                print(f"Blob '{self.blob_name}' ya existe. Continuando con el proceso.")
                return
            except ResourceNotFoundError:
                # El blob no existe
                content = json.dumps({
                    "created_at": datetime.datetime.now().isoformat(),
                    "created_by": self.node_id,
                    "leaders": []
                }).encode('utf-8')
                
                self.blob_client.upload_blob(content, overwrite=False)
                print(f"Blob '{self.blob_name}' creado para la elección de líder.")
        except Exception as e:
            print(f"Error al verificar o crear el blob: {str(e)}")
            # Si el error es por lease, simplemente continuamos
            if "LeaseIdMissing" in str(e):
                print("El blob ya está bajo control de un líder. Intentando adquirir liderazgo...")
    
    def try_acquire_leadership(self):
        #Intenta adquirir el liderazgo obteniendo un lease en el blob
        try:
            # Crear un cliente de lease para el blob
            lease_client = BlobLeaseClient(client=self.blob_client)
            
            # Intentar adquirir el lease
            self.lease_id = lease_client.acquire(lease_duration=self.lease_duration)
            self.is_leader = True
            
            # Actualizar el blob con la información del nuevo líder
            try:
                self._update_leader_info()
            except Exception as e:
                print(f"Error al actualizar información del líder, pero el lease fue adquirido: {str(e)}")
                # El nodo sigue siendo líder aunque no pudo actualizar la info
            
            print(f"¡Nodo {self.node_id} es ahora el LÍDER!")
            return True
        except Exception as e:
            if "LeaseAlreadyPresent" in str(e):
                current_leader = self.get_current_leader()
                leader_info = f"(posiblemente {current_leader['node_id']})" if current_leader else ""
                print(f"Otro nodo ya es el líder {leader_info}. Esperando...")
            else:
                print(f"No se pudo adquirir el liderazgo: {str(e)}")
            
            self.is_leader = False
            return False
    
    def _update_leader_info(self):
        #Actualiza la información del líder en el blob
        try:
            # Descargar contenido actual
            download = self.blob_client.download_blob(lease_id=self.lease_id)
            content = json.loads(download.readall().decode('utf-8'))
            
            # Añadir información del nuevo líder
            content["leaders"].append({
                "node_id": self.node_id,
                "acquired_at": datetime.datetime.now().isoformat(),
                "lease_id": self.lease_id
            })
            
            # Guardar cambios
            self.blob_client.upload_blob(json.dumps(content).encode('utf-8'), 
                                       overwrite=True, 
                                       lease_id=self.lease_id)
        except Exception as e:
            print(f"Error al actualizar la información del líder: {str(e)}")
            # Propagamos la excepción para que pueda ser manejada
            raise
    
    def renew_lease(self):
        #Renueva el lease para mantener el liderazgo
        if not self.is_leader or not self.lease_id:
            return False
        
        try:
            lease_client = BlobLeaseClient(client=self.blob_client, lease_id=self.lease_id)
            lease_client.renew()
            print(f"Lease renovado. El nodo {self.node_id} sigue siendo el LÍDER.")
            return True
        except Exception as e:
            print(f"Error al renovar el lease: {str(e)}")
            self.is_leader = False
            self.lease_id = None
            return False
    
    def release_leadership(self):
        #Libera voluntariamente el liderazgo
        if not self.is_leader or not self.lease_id:
            return
        
        try:
            lease_client = BlobLeaseClient(client=self.blob_client, lease_id=self.lease_id)
            lease_client.release()
            print(f"Liderazgo liberado por el nodo {self.node_id}.")
        except Exception as e:
            print(f"Error al liberar el liderazgo: {str(e)}")
        finally:
            self.is_leader = False
            self.lease_id = None
    
    def _heartbeat_loop(self):
        #Bucle de latido para mantener el liderazgo
        while self.running:
            if self.is_leader:
                if not self.renew_lease():
                    print("¡Perdido el liderazgo durante la renovación!")
                    # Intentar readquirir
                    time.sleep(5)  # Esperar un poco antes de intentar readquirir
                    self.try_acquire_leadership()
            else:
                # Si no somos líderes, intentamos adquirir el liderazgo
                self.try_acquire_leadership()
            
            # Esperar antes del próximo intento 
            time.sleep(max(5, self.lease_duration / 3))
    
    def start(self):
        #Inicia el proceso de elección de líder y el latido
        if self.running:
            return
        
        self.running = True
        print(f"Iniciando nodo {self.node_id}...")
        
        # Intentar adquirir el liderazgo inmediatamente
        self.try_acquire_leadership()
        
        # Iniciar el hilo de latido
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
    
    def stop(self):
        #Detiene el proceso de elección de líder
        if not self.running:
            return
        
        self.running = False
        print(f"Deteniendo nodo {self.node_id}...")
        
        # Liberar el liderazgo si somos líderes
        if self.is_leader:
            self.release_leadership()
        
        # Esperar a que el hilo de latido termine
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
    
    def get_current_leader(self):
        #Obtiene información sobre el líder actual
        try:
            # Intentamos descargar el blob sin especificar lease_id
            # Esto funcionará aunque no seamos el líder
            download = self.blob_client.download_blob()
            content = json.loads(download.readall().decode('utf-8'))
            
            if content["leaders"]:
                return content["leaders"][-1]
            return None
        except ResourceNotFoundError:
            # El blob no existe todavía
            print("Aún no se ha establecido ningún líder.")
            return None
        except Exception as e:
            print(f"Error al obtener información del líder actual: {str(e)}")
            # No debemos fallar completamente si no podemos obtener la info del líder
            return None

def simulate_node(account_name, account_key, container_name, node_name, duration=120):
    #Simula un nodo participando en la elección de líder
    try:
        node = LeaderElection(account_name, account_key, container_name, node_id=node_name)
        
        try:
            print(f"Iniciando simulación del nodo {node_name} por {duration} segundos...")
            node.start()
            
            # Ejecutar por la duración especificada
            end_time = time.time() + duration
            while time.time() < end_time:
                try:
                    status = "LÍDER" if node.is_leader else "seguidor"
                    current_leader = node.get_current_leader()
                    leader_info = f"(Líder actual: {current_leader['node_id']})" if current_leader else ""
                    
                    print(f"Nodo {node_name} es {status} {leader_info}")
                    
                    # Simular una caída aleatoria 
                    if node.is_leader and time.time() % 100 < 1:
                        print(f"¡Simulando caída del líder {node_name}!")
                        node.stop()
                        time.sleep(5)
                        node.start()
                except Exception as e:
                    print(f"Error durante la simulación: {str(e)}")
                time.sleep(10)
        finally:
            try:
                node.stop()
            except Exception as e:
                print(f"Error al detener el nodo: {str(e)}")
    except Exception as e:
        print(f"Error crítico que impide iniciar el nodo {node_name}: {str(e)}")
        

def main():
    parser = argparse.ArgumentParser(description="Simulador de Leader Election con Azure Blob Storage")
    parser.add_argument("--account-name", required=True, help="Nombre de la cuenta de Azure Storage")
    parser.add_argument("--account-key", required=True, help="Clave de la cuenta de Azure Storage")
    parser.add_argument("--container", default="leaderelection", help="Nombre del contenedor de blobs")
    parser.add_argument("--node-name", default=None, help="Nombre del nodo (por defecto: generado automáticamente)")
    parser.add_argument("--duration", type=int, default=120, help="Duración de la simulación en segundos")
    
    args = parser.parse_args()
    
    simulate_node(args.account_name, args.account_key, args.container, 
                 args.node_name or f"node-{uuid.uuid4()}", args.duration)

if __name__ == "__main__":
    main()