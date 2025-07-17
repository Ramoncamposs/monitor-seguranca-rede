# Perguntas e Respostas para Apresentação

Este documento contém possíveis perguntas que a professora pode fazer durante a apresentação do Monitor de Segurança para Redes Domésticas, junto com respostas sugeridas.

## Nota Importante sobre Firewalls e Escaneamento Local

Antes de prosseguir com as perguntas e respostas, é importante entender uma limitação técnica do escaneamento de portas: **o comportamento do escaneamento pode ser diferente quando você escaneia localhost (127.0.0.1) vs. quando escaneia de uma máquina externa**. Consulte o arquivo `LIMITACOES_FIREWALL.md` para uma explicação detalhada sobre este comportamento.

## Perguntas Conceituais

### 1. O que são portas de rede e por que é importante monitorá-las?

**Resposta:** Portas de rede são como "canais de comunicação" numerados em um dispositivo conectado à internet. Cada serviço (como um servidor web, e-mail, etc.) usa uma porta específica para se comunicar. É importante monitorá-las porque portas abertas são potenciais pontos de entrada para invasores. Conhecer quais portas estão abertas nos ajuda a identificar serviços desnecessários que podem representar riscos de segurança.

### 2. Qual a diferença entre uma porta aberta e uma porta fechada?

**Resposta:** Uma porta aberta significa que existe um programa ou serviço "escutando" naquela porta, pronto para receber conexões. Uma porta fechada não tem nenhum serviço ativo nela. No nosso programa, verificamos isso tentando estabelecer uma conexão com a porta - se conseguimos conectar, a porta está aberta; se não conseguimos, está fechada.

### 3. Por que algumas portas representam mais riscos que outras?

**Resposta:** Algumas portas são associadas a serviços que têm vulnerabilidades conhecidas ou que não são seguros por design. Por exemplo, a porta 23 (Telnet) transmite dados sem criptografia, incluindo senhas. Outras portas, como a 3389 (RDP - Remote Desktop Protocol), são frequentemente alvo de ataques de força bruta. Portas associadas a serviços essenciais e bem configurados representam menos riscos.

### 4. Por que é importante verificar se um dispositivo está acessível antes de escanear suas portas?

**Resposta:** Verificar a acessibilidade do dispositivo (usando ping) antes de escanear suas portas é importante por três motivos principais:
1. Evita tentar escanear dispositivos que não estão disponíveis, economizando tempo
2. Previne falsos negativos (quando todas as portas parecem fechadas, mas na verdade o dispositivo está inacessível)
3. Fornece feedback mais preciso ao usuário sobre o estado da rede

## Perguntas Técnicas

### 5. Como o programa consegue verificar se uma porta está aberta?

**Resposta:** O programa usa a biblioteca `socket` do Python para tentar estabelecer uma conexão TCP com o endereço IP e porta especificados. Se a conexão for bem-sucedida (retornar código 0), significa que a porta está aberta. Se falhar, a porta está fechada ou bloqueada. Definimos um timeout curto (1 segundo) para não esperar muito tempo por cada tentativa de conexão.

### 6. Como o programa descobre dispositivos na rede local?

**Resposta:** O programa primeiro identifica o IP da própria máquina para determinar a rede local. Depois, testa alguns IPs comuns nessa rede (como o gateway/roteador que geralmente termina em .1 e alguns outros dispositivos típicos) usando o comando ping. Os dispositivos que respondem ao ping são adicionados à lista de dispositivos acessíveis que podem ser escaneados.

### 7. Por que o programa escaneia apenas algumas portas e não todas as 65.535 possíveis?

**Resposta:** Escanear todas as 65.535 portas seria muito demorado e geraria muito tráfego na rede. Por isso, o programa foca nas portas mais comuns, onde geralmente rodam serviços importantes. Além disso, para um programa educacional e simples como este, é mais prático e didático focar em um conjunto menor de portas.

### 8. O programa pode ser detectado por sistemas de segurança?

**Resposta:** Sim. Muitos firewalls e sistemas de detecção de intrusão (IDS) podem identificar tentativas de escaneamento de portas como atividade suspeita. Por isso, o programa deve ser usado apenas em redes onde você tem permissão para fazer testes. Além disso, adicionamos pequenas pausas entre as verificações para tornar o escaneamento menos agressivo.

## Perguntas sobre o Código

### 9. Por que o projeto foi dividido em dois arquivos?

**Resposta:** Dividimos o projeto em dois arquivos para seguir o princípio de separação de responsabilidades:
- `network_scanner.py` contém a lógica técnica de descoberta de dispositivos e escaneamento de portas
- `main.py` cuida da interface com o usuário e do fluxo do programa

Isso torna o código mais organizado, mais fácil de entender e de manter. Se quisermos mudar a interface no futuro, podemos modificar apenas o `main.py` sem mexer na lógica de escaneamento.

### 10. O que significa o parâmetro `socket.AF_INET` usado no código?

**Resposta:** `socket.AF_INET` especifica a família de endereços que estamos usando, neste caso, o IPv4 (o formato de endereço IP mais comum, como 192.168.1.1). O Python também suporta outras famílias, como `AF_INET6` para IPv6. Junto com `socket.SOCK_STREAM`, estamos especificando que queremos criar um socket TCP, que é o protocolo usado para a maioria das conexões na internet.

### 11. Por que usamos um timeout no socket?

**Resposta:** Definimos um timeout (tempo limite) de 1 segundo para evitar que o programa fique esperando indefinidamente por uma resposta quando tenta se conectar a uma porta. Sem um timeout, se a porta estiver fechada ou bloqueada por um firewall, o programa poderia ficar "preso" esperando por muito tempo, tornando o escaneamento muito lento.

### 12. Como funciona o sistema de seleção de dispositivos por número?

**Resposta:** Quando o usuário executa a opção de descobrir dispositivos, o programa cria uma lista de IPs acessíveis. Cada IP recebe um número sequencial (1, 2, 3...). Nas outras opções do programa, em vez de digitar o IP completo, o usuário pode simplesmente selecionar o número correspondente ao dispositivo que deseja escanear. Isso torna o programa mais fácil de usar, especialmente para iniciantes, e reduz a chance de erros ao digitar endereços IP.

## Perguntas sobre Limitações e Melhorias

### 13. Quais são as limitações deste programa?

**Resposta:** Este programa tem várias limitações:
- Só verifica se a porta está aberta, não identifica vulnerabilidades específicas
- A descoberta de dispositivos é limitada a alguns IPs comuns, não escaneia toda a rede
- É relativamente lento, pois verifica uma porta de cada vez
- Não salva os resultados para comparação futura
- Funciona apenas com IPv4, não com IPv6
- Interface simples baseada em texto

### 14. Como este programa poderia ser melhorado no futuro?

**Resposta:** Algumas melhorias possíveis seriam:
- Adicionar escaneamento paralelo (usando threads) para verificar várias portas simultaneamente
- Implementar detecção de versão de serviços (banner grabbing)
- Criar uma interface gráfica mais amigável
- Adicionar suporte para salvar e comparar resultados
- Implementar uma descoberta de dispositivos mais completa usando ARP
- Adicionar mais regras de alerta baseadas em combinações de portas abertas

### 15. Este programa usa banco de dados?

**Resposta:** Não, esta versão simplificada não utiliza banco de dados. Todos os resultados são processados em tempo real e exibidos diretamente para o usuário. Os dados não são armazenados entre execuções do programa. Em uma versão mais avançada, poderíamos implementar um banco de dados para armazenar históricos de escaneamento e permitir comparações ao longo do tempo.

## Perguntas sobre Segurança e Ética

### 16. É legal usar este programa?

**Resposta:** É legal usar este programa apenas em redes e dispositivos que você possui ou tem permissão explícita para testar. Escanear portas em sistemas sem autorização pode ser ilegal em muitos países e violar políticas de uso aceitável de redes. Este programa foi desenvolvido para fins educacionais e para ajudar usuários a entenderem melhor a segurança de suas próprias redes domésticas.

### 17. Como este programa se relaciona com ferramentas profissionais de segurança?

**Resposta:** Este é um programa educacional muito básico comparado com ferramentas profissionais como Nmap, Wireshark ou soluções de monitoramento de rede empresariais. Ferramentas profissionais oferecem muito mais recursos, como:
- Detecção de sistemas operacionais
- Identificação precisa de serviços e versões
- Detecção de vulnerabilidades conhecidas
- Escaneamento avançado que evita detecção
- Geração de relatórios detalhados
- Monitoramento contínuo

Nosso programa serve como uma introdução simples aos conceitos de monitoramento de segurança de rede.
