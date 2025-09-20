from sqlalchemy.orm import Session

from model.security_manager import models as SecurityManager_models
from model.security_manager import crud as security_manager_crud
from model.security_manager import schemas as security_manager_schemas

from model.organization import models as Organization_models
from model.organization import crud as organization_crud
from model.organization import schemas as organization_schemas

from model.functional_unit import models as FunctionalUnit_models
from model.functional_unit import crud as functional_unit_crud

from model.department import models as Department_models    
from model.department import crud as department_crud

from model.team import models as Team_models
from model.team import crud as team_crud

from model.employee import models as Employee_models
from model.employee import crud as employee_crud

from model.pc import models as Pc_models
from model.pc import crud as pc_crud
from model.pc import schemas as pc_schemas

from model.router import models as Router_models
from model.router import crud as router_crud
from model.router import schemas as router_schemas

from model.behavior_log import models as BehaviorLog_models
from model.behavior_log import crud as behavior_log_crud
from model.behavior_log import schemas as behavior_logs_schemas
from model.behavior_log.init_behavior_log import BehaviorLogInserter

from model.pc.crud import set_pc_access_flag_by_id, get_ip_and_mac_address_by_id
from model.router.crud import get_router_by_connected_mac
from model.database import SessionLocal

import paramiko 
from typing import Optional, Tuple

class NetworkAccessController:
    """
    pc id 와 접근 제어 허용/차단 플래그(허용: true, 차단: false)를 받아, 
    해당 pc와 연결된 라우터의 ssh 에 접속해 방화벽 규칙을 추가/제거하는 클래스 
    """
    def __init__(self, db: Session, pc_id: str, access_flag : bool):
        self.db = db
        self.pc_id = pc_id
        self.access_flag = access_flag  
        
    def run(self):
        try:
            if self.access_flag:
                #접근 허용 
                set_pc_access_flag_by_id(self.db, self.pc_id, True)
                ip_address, mac_address = get_ip_and_mac_address_by_id(self.db, self.pc_id)
                if not ip_address or not mac_address:
                    return False

                allow_result = self._allow_network(ip_address, mac_address)
                if not allow_result:
                    print("네트워크 허용에 실패했습니다.")
                    return False
                return True
                
            else:
                #접근 차단
                set_pc_access_flag_by_id(self.db, self.pc_id, False)
                ip_address, mac_address = get_ip_and_mac_address_by_id(self.db, self.pc_id)
                if not ip_address or not mac_address:
                    print("IP 주소 또는 MAC 주소를 가져올 수 없습니다.")
                    return False

                block_result = self._block_network(ip_address, mac_address)
                if not block_result:
                    print("네트워크 차단에 실패했습니다.")
                    return False   
                return True 

        except Exception as e:
            print(f"Error occurred while checking PC anomaly: {e}")
            return

    def _block_network(self, ip_address, mac_address):
        try:
            print(f"Blocking network access for IP: {ip_address}, MAC: {mac_address}")
            router = get_router_by_connected_mac(self.db, mac_address)
            if not router:
                print(f"No router found for MAC address: {mac_address}")
                return
            
            print(f"Router found: {router.router_id}, Control IP: {router.control_ip}")
            
            control_ip = router.control_ip
            self._run_ssh_command_openwrt(
                host=control_ip,
                command=(
                    f"uci add_list firewall.anomaly_block.src_mac='{mac_address}' && "
                    f"uci set firewall.anomaly_block.enabled='1' && "
                    f"uci commit firewall && "
                    f"/etc/init.d/firewall restart"
                )
            )
            return True
        except Exception as e:
            print(f"Error blocking network access: {e}")
            return False   

    def _allow_network(self, ip_address, mac_address):
        try:
            print(f"Allowing network access for IP: {ip_address}, MAC: {mac_address}")
            router = get_router_by_connected_mac(self.db, mac_address)
            if not router:
                print(f"No router found for MAC address: {mac_address}")
                return
            
            print(f"Router found: {router.router_id}, Control IP: {router.control_ip}")
            
            control_ip = router.control_ip
            self._run_ssh_command_openwrt(
                host=control_ip,
                command=(
                    f"uci del_list firewall.anomaly_block.src_mac='{mac_address}' && "
                    f"[ -z \"$(uci -q get firewall.anomaly_block.src_mac)\" ] && "
                    f"uci set firewall.anomaly_block.enabled='0' && "
                    f"uci commit firewall && "
                    f"/etc/init.d/firewall restart"
                )
            )
            return True
        except Exception as e:
            print(f"Error Allowing network access: {e}")
            return False

    def _run_ssh_command_openwrt(self, host: str, command: str, *, port: int = 22,
                                username: str = "root", password: Optional[str] = "",
                                timeout: int = 8) -> Tuple[str, str]:
        # 1) Transport로 직접 붙기 (host key 교환)
        t = paramiko.Transport((host, port))
        t.banner_timeout = timeout
        t.connect()  # 서버 호스트키 교환

        try:
            try:
                t.auth_none(username)
            except paramiko.BadAuthenticationType as e:
                # 서버가 허용하는 인증 목록 확인
                allowed = set(e.allowed_types or [])
                # 3) keyboard-interactive 허용 시, 빈 응답으로 처리
                if "keyboard-interactive" in allowed:
                    def kbd_handler(title, instructions, prompts):
                        # 프롬프트 개수만큼 빈 문자열 반환 (빈 비번)
                        return ["" for _ in prompts]
                    t.auth_interactive(username, kbd_handler)
                # 4) password 허용 시, 빈 비번(또는 지정 비번)로 시도
                elif "password" in allowed:
                    t.auth_password(username, "" if password is None else password)
                else:
                    raise

            chan = t.open_session()
            chan.exec_command(command)
            out = chan.makefile("r").read().strip()
            err = chan.makefile_stderr("r").read().strip()
            chan.close()
            return out, err

        finally:
            t.close()

# 모듈 테스트 코드
# with SessionLocal() as db:
#     networkaccesscontroller = NetworkAccessController(db, "PC-8865", access_flag=True)
#     networkaccesscontroller.run()