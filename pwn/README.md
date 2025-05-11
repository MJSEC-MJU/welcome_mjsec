## 기술 스택

- **언어**: C
- **컴파일러**: GCC (GNU Compiler Collection)
- **디버깅 & 리버스 엔지니어링**
  - GDB (with pwndbg)
  - objdump, readelf, strings
- **스크립팅**: Python 3 (플래그 복호화 스크립트)
- **운영체제**: Linux (x86_64)
- **버전 관리**: Git

근데
지피티 2분컷 문제.
그리고 gdb 에서 jump print_flag 하면 걍 flag 나옴
그렇다고 심볼을 없애기에는 print_flag주소를 알수없음
그냥 문제 설명에 주소알아내서 exploit 하라는 수밖에

컴파일
