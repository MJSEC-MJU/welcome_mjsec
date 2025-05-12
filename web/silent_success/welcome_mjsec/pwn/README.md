# SimplePwn

⚠️ **취약점 (Vulnerabilities)**  
단순 버퍼 오버플로우

📌 **기술 스택 (Tech Stack)**

| 분야              | 사용 기술                                    |
| ----------------- | -------------------------------------------- |
| 언어              | C                                            |
| 컴파일러          | GCC (GNU Compiler Collection)                |
| 디버깅/익스플로잉 | GDB (with pwndbg), objdump, readelf, strings |
| 스크립팅          | Python 3 (pwntools 기반 익스플로잇 스크립트) |
| 운영체제          | Linux (x86_64)                               |
| 버전 관리         | Git                                          |

📝 **문제**  
버퍼 크기 검증이 없는 취약한 함수에 과도한 입력을 전달해 스택을 오버플로우시킨 후, `print_flag` 함수의 주소로 반환 주소를 덮어써 `print_flag()`를 호출하면 `MJSEC{W3ll_cOm3_T0_tH3_H311}` 플래그를 출력하는 간단한 Pwnable 문제입니다.

근데
지피티 2분컷 문제.
그리고 gdb 에서 jump print_flag 하면 걍 flag 나옴
그렇다고 심볼을 없애기에는 print_flag주소를 알수없음
그냥 문제 설명에 주소알아내서 exploit 하라는 수밖에

컴파일
