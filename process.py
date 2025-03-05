import time
from kazoo.client import KazooClient

# Connect to ZooKeeper
zk = KazooClient(hosts='127.0.0.1:2181')
zk.start()

election_path = "/leader_election"

# Ensure the leader election path exists
if not zk.exists(election_path):
    zk.create(election_path)

# Create an ephemeral sequential znode
node_path = zk.create(election_path + "/node_", ephemeral=True, sequence=True)
node_name = node_path.split("/")[-1]

print(f"[{node_name}] Created node.")

def watch_leader():
    """
    Watch the current leader. If it disappears, trigger re-election.
    """
    children = zk.get_children(election_path)
    children.sort()

    leader_node = children[0]
    leader_path = f"{election_path}/{leader_node}"

    if node_name == leader_node:  # This node is the leader
        print(f"[{node_name}] I am the leader!")
        return

    print(f"[{node_name}] Watching leader {leader_node} for failure...")

    @zk.DataWatch(leader_path)
    def on_leader_delete(data, stat):
        if stat is None:  # Leader is gone
            print(f"[{node_name}] Leader {leader_node} failed! Re-electing...")
            watch_leader()  # Re-run leader election logic

# Start watching the leader
watch_leader()

# Keep the process running
while True:
    time.sleep(1)
