# Monitor de Segurança para Redes Domésticas - Versão Simplificada

Este é um programa simples para monitorar a segurança de redes domésticas, desenvolvido para o trabalho de Aplicações em Rede. O programa descobre dispositivos na rede local, verifica quais portas estão abertas e alerta sobre possíveis vulnerabilidades.

## Estrutura do Projeto

O projeto é composto por apenas dois arquivos:

1. `network_scanner.py` - Contém as funções básicas para descobrir dispositivos e escanear portas
2. `main.py` - Interface de texto simples para interagir com o usuário

## Como Executar

1. Certifique-se de ter o Python 3 instalado no seu computador
2. Baixe os dois arquivos para uma mesma pasta
3. Abra o terminal ou prompt de comando na pasta onde estão os arquivos
4. Execute o comando: `python main.py`
5. Siga as instruções na tela

## Funcionalidades

O programa oferece quatro funcionalidades principais:

1. **Descobrir dispositivos na rede** - Encontra dispositivos acessíveis na sua rede local
2. **Escanear portas comuns** - Verifica as portas mais utilizadas (21, 22, 23, 25, 53, 80, 443, 3306, 3389) em um dispositivo selecionado
3. **Verificar uma porta específica** - Permite escolher uma porta específica para verificar em um dispositivo selecionado
4. **Sobre o programa** - Exibe informações sobre o programa e a importância da segurança de portas

## Como o Programa Funciona

### Fluxo de Execução

1. O arquivo `main.py` é o ponto de entrada do programa
2. A função `main()` exibe o menu principal e processa a escolha do usuário
3. Dependendo da escolha, o programa chama diferentes funções:
   - Opção 1: `descobrir_dispositivos()` - Encontra dispositivos na rede
   - Opção 2: `escanear_portas_comuns()` - Verifica portas comuns em um dispositivo
   - Opção 3: `verificar_porta_especifica()` - Verifica uma porta específica
   - Opção 4: `sobre_programa()` - Mostra informações sobre o programa
   - Opção 5: Encerra o programa

### Interação entre os Arquivos

- O arquivo `main.py` importa as funções `scan_port`, `scan_common_ports`, `ping_host` e `discover_network_ips` do arquivo `network_scanner.py`
- Quando o usuário escolhe descobrir dispositivos ou escanear portas, o `main.py` chama as funções do `network_scanner.py` para realizar o trabalho técnico
- O `main.py` se preocupa com a interface e interação com o usuário
- O `network_scanner.py` se preocupa com a lógica de descoberta de dispositivos e escaneamento de portas

### Como a Descoberta de Dispositivos Funciona

1. O programa obtém o IP da própria máquina para determinar a rede local
2. Testa alguns IPs comuns na rede (como o gateway/roteador e alguns dispositivos típicos)
3. Para cada IP, envia um comando de ping para verificar se o dispositivo está acessível
4. Cria uma lista de dispositivos acessíveis para o usuário selecionar

### Como o Escaneamento de Portas Funciona

1. O programa verifica primeiro se o dispositivo está acessível usando ping
2. Se estiver acessível, cria um socket (uma conexão de rede)
3. Tenta se conectar ao endereço IP e porta especificados
4. Se a conexão for bem-sucedida, a porta está aberta
5. Se a conexão falhar, a porta está fechada
6. O programa repete esse processo para cada porta que precisa verificar

## Conceitos Importantes

### O que são Portas?

Portas são como "canais de comunicação" em um dispositivo conectado à rede. Cada serviço (como um servidor web, e-mail, etc.) usa uma porta específica. Por exemplo:

- Porta 80: Usada para tráfego web (HTTP)
- Porta 443: Usada para tráfego web seguro (HTTPS)
- Porta 22: Usada para acesso remoto seguro (SSH)

### Por que Monitorar Portas?

- Portas abertas são pontos de entrada potenciais para invasores
- Conhecer quais portas estão abertas ajuda a identificar serviços desnecessários
- Fechar portas não utilizadas melhora a segurança da rede

### Por que Verificar se o Dispositivo está Acessível?

- Evita tentar escanear dispositivos que não estão disponíveis
- Economiza tempo ao não tentar conexões que certamente falharão
- Fornece resultados mais precisos, evitando falsos negativos
