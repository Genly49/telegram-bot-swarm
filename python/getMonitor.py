import requests
import datetime
import matplotlib.pyplot as plt
import json
import pandas as pd
import ace_tools_open as tools

PROM_URL = "http://localhost:9090"

PROMQL_QUERIES = {
        "/node_cpu": lambda target: f'(1 - (rate(node_cpu_seconds_total{{mode="idle",instance="{target}:9100"}}[1m])))',
        "/node_ram": lambda target: f'node_memory_MemAvailable_bytes{{instance="{target}:9100"}} / node_memory_MemTotal_bytes{{instance="{target}:9100"}}',
        "/node_disk": lambda target: f'node_filesystem_avail_bytes{{mountpoint="/",instance="{target}:9100"}} / node_filesystem_size_bytes{{mountpoint="/",instance="{target}:9100"}}',
        "/node_rx": lambda target: f'rate(node_network_receive_bytes_total{{instance="{target}:9100"}}[1m])',
        "/node_tx": lambda target: f'rate(node_network_transmit_bytes_total{{instance="{target}:9100"}}[1m])',
        "/node_load": lambda target: f'node_load1{{instance="{target}:9100"}}',
    	"/container_cpu": lambda target: f'rate(container_cpu_usage_seconds_total{{name="{target}"}}[1m]) * 100',
    	"/container_ram": lambda target: f'container_memory_usage_bytes{{name="{target}"}}',
    	"/container_rx": lambda target: f'rate(container_network_receive_bytes_total{{name="{target}"}}[1m])',
    	"/container_tx": lambda target: f'rate(container_network_transmit_bytes_total{{name="{target}"}}[1m])',
        "/container_cpu_label": lambda target: f'rate(container_cpu_usage_seconds_total{{container_label_app="{target}"}}[1m]) * 100',
        "/container_ram_label": lambda target: f'container_memory_usage_bytes{{container_label_app="{target}"}}',
        "/container_rx_label": lambda target: f'rate(container_network_receive_bytes_tota{{container_label_app="{target}"}}l[1m])',
        "/container_tx_label": lambda target: f'rate(container_network_transmit_bytes_total{{container_label_app="{target}"}}[1m])',
        "/container_cpu_label": lambda target: f'rate(container_cpu_usage_seconds_total{{container_label_character="{target}"}}[1m]) * 100',
        "/container_ram_label": lambda target: f'container_memory_usage_bytes{{container_label_character="{target}"}}',
        "/container_rx_label": lambda target: f'rate(container_network_receive_bytes_total{{container_label_character="{target}"}}[1m])',
        "/container_tx_label": lambda target: f'rate(container_network_transmit_bytes_total{{container_label_character="{target}"}}[1m])'
}

def query_prometheus(target, promql, step = "30") :
    end_time = datetime.datetime.today()
    start_time = end_time - datetime.timedelta(minutes = 30)
    try :
        print(end_time)
        print(start_time)
        query = PROMQL_QUERIES[promql](target)
        response = requests.get(f"{PROM_URL}/api/v1/query_range", params = {
            "query": query,
            "start": start_time.timestamp(),
            "end": end_time.timestamp(),
            "step": step
        })
        result = response.json()
        print(query)
        print(result)
        if result["status"] == "success" and result["data"]["result"] :
            result_data = result["data"]["result"][0]
            values = result_data["values"]
            timestamps = [datetime.datetime.fromtimestamp(float(t)) for t, _ in values]
            data = [float(v) for _, v in values]

            json_output = {
                "metric": result_data["metric"],
                "values": values
            }

            preview_json = json.dumps(json_output["values"][:5], indent = 2)
            df = pd.DataFrame(json_output["values"], columns = ["timestamp", "value"])
            tools.display_dataframe_to_user(name = "Prometheus 查詢結果 (前幾筆)", dataframe = df.head())

            plt.figure(figsize = (10, 4))
            plt.plot(timestamps, data, label = promql)
            plt.title(f"{promql}_usage".replace("/", ""))
            plt.xlabel("Time")
            plt.ylabel("Value") if "rx" in promql or "tx" in promql else plt.ylabel("Percentage")
            plt.xticks(rotation = 30)
            plt.grid(True)
            plt.tight_layout()
            plt.legend()
            image_path = f"/tmp/{target}_{promql.replace('/', '')}.png"
            plt.savefig(image_path)
            plt.close()
            return image_path
        else :
            return "No queries"

    except Exception as e :
        print(f"Prometheus 查詢錯誤：{e}")
        return "No queries"
