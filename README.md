# Patrón de Elección de Líder

## Resumen

La **elección de líder** es un patrón de computación distribuida donde un nodo es designado como "líder" y se encarga de tareas específicas que requieren coordinación. Este patrón se usa en sistemas distribuidos para garantizar exclusividad en el acceso a recursos o para coordinar la ejecución de tareas.

## Casos de Uso

- **Bases de datos distribuidas**: El líder maneja tareas críticas como la resolución de conflictos.
- **Programación de tareas**: El líder se encarga de distribuir y coordinar las tareas.
- **Algoritmos de consenso**: Protocolos como Raft o Paxos usan elección de líder para mantener la coherencia entre nodos.

## Conceptos Clave

- **Líder**: Nodo responsable de realizar tareas o coordinar acciones.
- **Seguidor**: Nodo que sigue las instrucciones del líder.
- **Proceso de Elección**: Mecanismo por el cual los nodos deciden cuál será el líder.
- **Failover**: Si el líder falla, otro nodo es elegido para tomar su lugar.

## Algoritmos Comunes

1. **Algoritmo Bully**: El nodo con la ID más alta es elegido como líder. Si el líder falla, los demás nodos inician una nueva elección.
2. **Algoritmo de Anillo**: Los nodos están organizados en un anillo lógico. Si el líder falla, la elección se propaga alrededor del anillo hasta elegir uno nuevo.
3. **Paxos**: Algoritmo de consenso que incluye elección de líder para mantener un valor común entre nodos.
4. **Raft**: Utilizado en sistemas como bases de datos distribuidas para garantizar la consistencia mediante la elección de un líder.

## Tolerancia a Fallos

La elección de líder debe manejar posibles fallos de nodos o particiones de red. Esto se logra mediante:

- **Tiempos de espera y reintentos**: Los nodos detectan fallos y desencadenan una nueva elección.
- **Sistemas basados en quórum**: Se requiere el consenso de una mayoría de nodos para elegir al líder y evitar problemas como el "split-brain".

## Ejemplo en Bases de Datos Distribuidas (MongoDB)

MongoDB utiliza elección de líder en su conjunto de réplicas. Si el nodo primario falla, se elige automáticamente un nuevo primario.

## Ventajas

- **Tolerancia a fallos**: Garantiza la continuidad del sistema incluso si el líder falla.
- **Simplicidad**: El líder centraliza la coordinación de tareas.
- **Escalabilidad**: La elección de líder puede escalar con el número de nodos.

## Desventajas

- **Sobrecarga**: El proceso de elección genera comunicaciones adicionales.
- **Punto único de falla**: Aunque hay failover, el sistema depende de un solo nodo para ciertas tareas.
- **Complejidad**: Implementar elección de líder con tolerancia a fallos puede ser complejo.

## Conclusión

La elección de líder es un patrón clave en sistemas distribuidos, proporcionando coordinación, consistencia y tolerancia a fallos. Es fundamental en escenarios donde se necesita un nodo responsable para ejecutar tareas críticas.
