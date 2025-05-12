
FROM i386/ubuntu

RUN apt update && apt install -y gcc gdb make

WORKDIR /ctf

COPY . .

RUN make && chmod +x nullified_intent && chmod 444 flag

CMD ["./nullified_intent"]
