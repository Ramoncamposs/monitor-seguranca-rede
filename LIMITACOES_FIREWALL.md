# Limitações do Scanner de Portas e Comportamento com Firewalls

Este documento explica algumas limitações importantes do nosso scanner de portas, especialmente em relação ao comportamento com firewalls e ao escanear o localhost (127.0.0.1).

## Escaneamento de Localhost vs. IPs Externos

### O Problema do Localhost

Quando você escaneia o localhost (127.0.0.1), pode encontrar resultados diferentes do que ao escanear o mesmo computador a partir de outra máquina. Isso acontece porque:

1. **Conexões de Loopback**: Conexões para 127.0.0.1 são conexões de loopback que não passam pela pilha de rede completa
2. **Bypass de Firewall**: Muitos firewalls são configurados para filtrar tráfego externo, mas não filtram conexões internas (loopback)
3. **Falsos Positivos**: Uma porta pode aparecer como "aberta" no localhost mesmo quando está bloqueada para conexões externas

### Exemplo Prático

Se você configurar o firewall para bloquear a porta 22 (SSH) com:
```
sudo ufw deny 22
```

E depois escanear o localhost, a porta 22 ainda pode aparecer como aberta porque:
- O tráfego de loopback (127.0.0.1 → 127.0.0.1) geralmente não passa pelo filtro de pacotes do firewall
- O serviço SSH ainda está em execução e aceitando conexões localmente

## Como Nosso Scanner Tenta Lidar com Isso

Nossa versão atualizada do scanner tenta detectar se uma porta está bloqueada pelo firewall:

1. Primeiro verifica se a conexão inicial é bem-sucedida
2. Se for bem-sucedida e o IP for 127.0.0.1, tenta verificar as regras de firewall (UFW e iptables)
3. Se detectar regras de bloqueio para a porta, marca como "BLOQUEADA POR FIREWALL"

No entanto, esta detecção:
- Só funciona em sistemas Linux
- Requer permissões de sudo para verificar as regras de firewall
- Pode não detectar todas as configurações de firewall

## Recomendações para Testes Mais Precisos

Para obter resultados mais precisos sobre a segurança real da sua rede:

1. **Teste a partir de outra máquina**: Escaneie seu computador a partir de outro dispositivo na rede
2. **Compare resultados**: Compare os resultados de escanear localhost vs. escanear o IP externo do mesmo computador
3. **Use ferramentas profissionais**: Para testes mais completos, considere usar ferramentas como Nmap

## Limitações Técnicas do Nosso Scanner

Nosso scanner é educacional e tem várias limitações:

1. **Detecção de Firewall Limitada**: Só verifica regras básicas de UFW e iptables em Linux
2. **Sem Detecção de Filtros Stateful**: Não detecta firewalls stateful que permitem apenas conexões estabelecidas
3. **Sem Detecção de Proxy/NAT**: Não detecta se há proxies ou NAT entre o scanner e o alvo
4. **Sem Fingerprinting**: Não identifica versões de serviços ou sistemas operacionais

## Conclusão

O comportamento diferente ao escanear localhost vs. IPs externos é uma característica importante para entender em segurança de redes. Nosso scanner tenta lidar com isso de forma educacional, mas é importante estar ciente dessas limitações ao interpretar os resultados.
