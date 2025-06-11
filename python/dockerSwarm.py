import datetime
import docker

def list_nodes(client) :
    try :
        nodes = client.nodes.list()
        node_info_list = []

        for node in nodes :
            attrs = node.attrs
            hostname = attrs["Description"]["Hostname"]
            ip = attrs["Status"]["Addr"]
            status = attrs["Status"]["State"]
            availability = attrs["Spec"]["Availability"]
            manager_status = attrs.get("ManagerStatus", {}).get("Leader", False)
            manager_str = "Leader" if manager_status else ("Reachable" if "ManagerStatus" in attrs else "Worker")

            node_info_list.append({
                "hostname": hostname,
                "ip": ip,
                "status": status,
                "availability": availability,
                "manager_status": manager_str
            })
        return node_info_list
    except Exception as e :
        print(f"節點查詢失敗：{e}")
        return "查詢節點失敗或未啟用 Docker Swarm。"

def format_ports(port_dict) :
    if not port_dict :
        return "無"
    parts = []
    for port, bindings in port_dict.items() :
        if bindings is None :
            parts.append(port)
        else :
            for bind in bindings :
                parts.append(f"{bind['HostIp']}:{bind['HostPort']}->{port}")
    return ", ".join(parts)

def list_containers(client, target) :
    try :
        containers = client.containers.list(all = True)
        result = []

        for c in containers :
            attrs = c.attrs
            created_time = datetime.datetime.strptime(attrs["Created"][:19], "%Y-%m-%dT%H:%M:%S")
            created_time_str = created_time.strftime("%Y-%m-%d %H:%M:%S")
            nano_cpus = attrs["HostConfig"].get("NanoCpus", 0)
            cpu_limit = f"{nano_cpus / 1e9:.2f} CPU" if nano_cpus else "不限"
            memory = attrs["HostConfig"].get("Memory", 0)
            ram_limit = f"{memory / (1024**2):.0f} MB" if memory else "不限"
            ports = format_ports(attrs["NetworkSettings"].get("Ports", {}))
            result.append({
                "name": c.name,
                "status": c.status,
                "ports": ports,
                "cpu": cpu_limit,
                "memory": ram_limit,
                "created": created_time_str
            })
        return result if result else "此節點沒有任何容器。"

    except Exception as e :
        print(f"Docker 錯誤：{e}")
        return "查詢失敗，無法連線到 Docker。"

def list_services(client) :
    try :
        services = client.services.list()
        result = []

        for s in services :
            spec = s.attrs.get("Spec", {})
            name = spec.get("Name", "-")
            image = spec.get("TaskTemplate", {}).get("ContainerSpec", {}).get("Image", "-")

            mode = spec.get("Mode", {})
            desired = mode.get("Replicated", {}).get("Replicas", 1)
            try :
                tasks = s.tasks()
                running = sum(1 for t in tasks if t["Status"]["State"] == "running")
            except :
                running = "?"
            replicas = f"{running}/{desired}"

            ports = "-"
            port_info = s.attrs.get("Endpoint", {}).get("Ports", [])
            if port_info:
                ports = ", ".join(f"{p['PublishedPort']}->{p['TargetPort']}" for p in port_info)

            result.append({
                "name": name,
                "image": image,
                "replicas": replicas,
                "ports": ports
            })
        return result if result else "沒有任何服務。"

    except Exception as e :
        return f"列出服務失敗：{e}"

def create_container(client, name, image, ports) :
    try :
        container = client.containers.create(image = image, name = name, ports = ports)
        return f"已建立容器（未啟動）：{name}"
    except Exception as e :
        return f"建立失敗：{e}"

def start_container(client, name) :
    try :
        container = client.containers.get(name)
        container.start()
        return f"已啟動容器：{name}"
    except Exception as e :
        return f"啟動失敗：{e}"

def run_container(client, name, image, ports) :
    try :
        container = client.containers.run(image = image, name = name, ports = ports, detach = True)
        return f"已建立並啟動容器：{name}"
    except Exception as e :
        return f"啟動失敗：{e}"

def pause_container(client, name) :
    try :
        container = client.containers.get(name)
        container.pause()
        return f"已暫停容器：{name}"
    except Exception as e :
        return f"暫停失敗：{e}"

def resume_container(client, name) :
    try :
        container = client.containers.get(name)
        container.unpause()
        return f"已恢復容器：{name}"
    except Exception as e :
        return f"恢復失敗：{e}"

def restart_container(client, name) :
    try :
        container = client.containers.get(name)
        container.restart()
        return f"已重新啟動容器：{name}"
    except Exception as e :
        return f"重啟失敗：{e}"

def remove_container(client, name) :
    try :
        container = client.containers.get(name)
        container.remove(force=True)
        return f"已刪除容器：{name}"
    except Exception as e :
        return f"刪除失敗：{e}"

def create_service(client, name, image, port, replicas = 1) :
    try :
        endpoint = docker.types.EndpointSpec(ports = {port: port})
        mode = docker.types.ServiceMode("replicated", replicas = replicas)
        service = client.services.create(
            name = name,
            image = image,
            endpoint_spec = endpoint,
            mode = mode
        )
        return f"已建立服務：{name}"
    except Exception as e :
        return f"建立服務失敗：{e}"

def remove_service(client, name) :
    try :
        service = client.services.get(name)
        service.remove()
        return f"已刪除服務：{name}"
    except Exception as e :
        return f"刪除服務失敗：{e}"

def restart_service(client, name, image, port, replicas = 1) :
    try :
        try :
            service = client.services.get(name)
            service.remove()
        except :
            pass
        endpoint = docker.types.EndpointSpec(ports = {port: port})
        mode = docker.types.ServiceMode("replicated", replicas = replicas)
        client.services.create(
            name = name,
            image = image,
            endpoint_spec = endpoint,
            mode = mode
        )
        return f"已重啟服務：{name}"
    except Exception as e :
        return f"重啟服務失敗：{e}"
