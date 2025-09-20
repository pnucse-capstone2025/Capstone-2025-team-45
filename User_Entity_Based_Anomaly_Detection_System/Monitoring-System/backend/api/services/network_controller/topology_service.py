from sqlalchemy.orm import Session

from model.router.crud import get_routers_by_organization_id
from model.pc.crud import get_pcs_by_organization_id

def genereate_topology_for_organization(db: Session, organization_id: str):
    """
    조직에 속한 라우터와 PC의 토폴로지를 생성합니다.
    """
    #  조직에 속한 라우터/PC 조회
    routers = get_routers_by_organization_id(db, organization_id)
    pcs = get_pcs_by_organization_id(db, organization_id)

    # 노드 생성
    nodes = []
    for r in routers:
        nodes.append({
            "id": f"Router-{r.router_id}",
            "type": "router",
            "data": {"label": f"Router-{r.router_id}"},
            "position": {"x": 100, "y": 100}, 
            "state": {r.state}
        })

    for p in pcs:
        nodes.append({
            "id": f"{p.pc_id}",
            "type": "pc",
            "data": {"label": f"{p.pc_id}"},
            "position": {"x": 300, "y": 100},  
            "state": {p.current_state},
            "present_user_id": p.present_user_id,
            "access_flag": {p.access_flag},

            "ip_address": {p.ip_address},
            "mac_address": {p.mac_address},
        })

    edges = []
    for router in routers:
        if not router.connected_mac_addresses:  
            continue
        for mac in router.connected_mac_addresses:
            for pc in pcs:
                if pc.mac_address == mac:
                    edges.append({
                        "id": f"edge-{router.router_id}-{pc.pc_id}",
                        "source": f"Router-{router.router_id}",
                        "target": f"{pc.pc_id}",
                        "type": "default"
                    })
    return nodes, edges