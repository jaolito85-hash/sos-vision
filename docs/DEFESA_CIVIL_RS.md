# SOS VISION · Defesa Civil — Blueprint Rio Grande do Sul
## Sistema Operacional de Coordenação de Resgate em Massa via WhatsApp
### Documento de design · Junho/2026

> Recorte deste documento: **apenas a vertical V1 (Defesa Civil — enchente, alagamento, deslizamento)**, especializada para a realidade do Rio Grande do Sul. Deriva do `PLATAFORMA_SOS_VISION.md`, mas aprofunda e, em alguns pontos, **corrige** o desenho genérico com base nas lições de maio/2024.

---

## 0. A tese (o que muda em relação ao doc fundador)

O doc fundador modela Defesa Civil como o mesmo padrão das outras verticais: **vítima aciona → sala recebe → operador despacha**. Esse é o modelo de emergência *individual*.

Uma enchente no RS não é individual. É um **evento de massa simultâneo**, e o que matou pessoas e gerou caos em 2024 **não foi a falta de pedidos de socorro — foi a falta de coordenação dos resgates**.

> **Tese RS:** o produto não é um "botão de pânico". É um **sistema operacional de coordenação de resgate em massa**. Recebe o SOS pelo WhatsApp, mas o moat é:
> 1. **Despachar a frota certa pro lugar certo sem duplicar** (anti-duplicação foi a dor #1 de 2024).
> 2. **Localização que funciona quando o endereço não funciona** (rua alagada, vítima no telhado).
> 3. **Rede que continua de pé quando a internet cai** (torres alagadas/sem energia).
> 4. **Saber onde estão os vulneráveis ANTES** de virarem resgate (acamados, O₂-dependentes, diálise).

Tudo abaixo serve a essas quatro frases.

---

## 1. Lições de maio/2024 → requisitos de produto

| O que aconteceu em 2024 | Requisito que isso vira |
|---|---|
| SOS coordenado em planilhas Google e mapas improvisados | **Fonte única de verdade** com estado por vítima (aguardando / em rota / resgatado) e dedup automático |
| Pessoas **já resgatadas continuavam na lista** → barcos indo em vão | **Ciclo de vida do resgate com confirmação** e baixa automática (quem resgatou marca; vizinhos confirmam) |
| Dois voluntários no mesmo telhado, outro telhado esquecido | **Despacho com lock geográfico** — um chamado só pode estar "assumido" por uma equipe |
| Torres de celular caíram | **Resiliência**: buffer offline, payload leve, SMS fallback, ponte satélite (Starlink) |
| Endereço inútil (rua submersa, ponto de referência debaixo d'água) | **Localização precisa**: GPS + what3words/Plus Codes + **andar/telhado** + foto georreferenciada |
| Mortes de acamados/idosos não evacuados | **Cadastro prévio de vulneráveis** por área de risco + evacuação preventiva priorizada |
| Caos de abrigos; gente não ia por causa de **pets** | **Mapa de abrigos** com vaga em tempo real e flag pet-friendly |
| "Cadê minha mãe?" — famílias separadas | **Reunificação familiar** (registro de procurados + match) |
| Voluntários de barco/jet-ski sem coordenação | **App de campo leve** para a frota (web/PWA, funciona no celular molhado e sem teclado) |

---

## 2. O ciclo da enchente — e o que o sistema faz em cada fase

O sistema não "liga" na hora do resgate. Ele acompanha as 5 fases:

### Fase 1 — Vigilância & Alerta (horas a dias antes)
- Ingestão de dados hidrológicos: **CEMADEN** (chuva/risco), **ANA/SGB-CPRM** (cota de rios), **régua do Guaíba**, **MetSul/INMET** (previsão).
- Quando um gatilho dispara (cota prevista > X em Y horas, ou alerta CEMADEN nível laranja/vermelho), a Defesa Civil **arma um evento** e o sistema calcula o **geofence de impacto** (polígono que vai alagar).
- Broadcast preventivo por template aprovado pra todos os cadastrados dentro do geofence.

### Fase 2 — Evacuação preventiva (a janela que salva mais vidas)
- Broadcast: *"Chuva forte chegando à sua região. Você está bem? Responda **1** (em casa/seguro), **2** (já saí), **3** (preciso de ajuda agora)."*
- **Quem não responde em X min → status DESCONHECIDO** (amarelo no mapa) — não é ignorado, é fila de verificação ativa.
- Vulneráveis cadastrados (acamados, O₂, diálise, idoso só, criança pequena) entram numa **lista de evacuação prioritária** que a Defesa Civil trabalha proativamente.
- Bot envia **rota de fuga e abrigo mais próximo com vaga** — calculada evitando vias já alagadas.

### Fase 3 — Resgate ativo (o pico)
- Quem responde **3**, ou manda foto/áudio/vídeo, ou aciona link salvo → **chamado de resgate** criado.
- IA classifica gravidade e popula a fila por prioridade.
- Sala **despacha** a equipe de campo mais próxima e disponível (bombeiro, brigada, voluntário cadastrado).
- Vítima recebe **token-link** e passa a transmitir GPS ao vivo; recebe ETA ("equipe a caminho").

### Fase 4 — Abrigo & Reunificação
- Resgatado → encaminhado a abrigo com vaga; **check-in no abrigo** atualiza o estado (sai da fila de resgate).
- Módulo de **reunificação**: quem procura alguém registra; match por nome/telefone/foto/abrigo.

### Fase 5 — Pós-evento
- Relatório automático por evento: tempo médio de resposta, % cobertura GPS, vidas atendidas, mapa de calor.
- Mensagem de acompanhamento 24–72h depois.
- Dados agregados anonimizados pro gestor planejar a próxima estação.

---

## 3. Atores e seus painéis

| Ator | Como interage | Painel |
|---|---|---|
| **Cidadão em risco** | WhatsApp + token-link PWA | Conversa do bot + página de rastreamento leve |
| **Vulnerável pré-cadastrado** | Cadastro prévio via WhatsApp | (mesmo acima, com prioridade) |
| **Operador da sala (Defesa Civil)** | Web — Sala de Comando | Mapa, fila, despacho, chat humano, audit |
| **Equipe de campo** (bombeiro/brigada/voluntário) | PWA de campo no celular | Lista "meus chamados", navegação, botão "resgatado" |
| **Coordenador de abrigo** | PWA simples | Lance de vagas, check-in/out, flags (pet, médico) |
| **Gestor / prefeito** | Dashboard read-only | KPIs, mapa de calor, vidas atendidas |
| **Familiar buscando alguém** | WhatsApp / página pública | Fluxo de reunificação |

---

## 4. Fluxos de WhatsApp (Cloud API oficial)

> Premissa: **WhatsApp Cloud API (Meta Business)** pela estabilidade e templates de broadcast no pico. Camada de mensageria abstrata permite SMS/satélite como fallback (ver §6.3).

### 4.1 Cadastro prévio do morador de área de risco (proativo, fora da crise)
```
Bot: Olá! Sou o Guardião da Defesa Civil de {município}.
     Quer se cadastrar para receber proteção em enchentes? (Sim/Não)
→ nome → confirma endereço (ou compartilha localização) → quantas pessoas na casa?
→ Há alguém que precisa de atenção especial?
   [ ] Acamado   [ ] Usa oxigênio   [ ] Faz diálise
   [ ] Idoso(a) sozinho(a)   [ ] Criança < 2 anos   [ ] Cadeirante   [ ] Nenhum
→ Tem animais? (importante p/ escolher abrigo)
→ Contato de confiança (telefone)
✓ Pronto. Salve este contato. Em emergência, toque aqui: {link}
```
O resultado popula `pessoas_protegidas` + georreferencia a casa dentro/fora dos geofences de risco já desenhados pela Defesa Civil.

### 4.2 Broadcast de alerta + triagem (Fase 2)
```
[TEMPLATE aprovado, disparo em massa por geofence]
⚠️ Alerta da Defesa Civil de {município}
Chuva/cheia forte prevista para sua região nas próximas {N}h.
Você está bem agora?
  1️⃣ Estou em casa, seguro
  2️⃣ Já saí / lugar seguro
  3️⃣ PRECISO DE AJUDA
```
- **1** → registra OK (verde), envia orientação preventiva + abrigo mais próximo.
- **2** → registra evacuado (azul), pergunta se chegou a abrigo.
- **3** → abre chamado de resgate, pede localização ao vivo, sobe pra fila.
- **sem resposta** → amarelo (desconhecido) na lista de verificação.
- **foto/vídeo/áudio espontâneo** → IA classifica → chamado.

### 4.3 Disparo de resgate (Fase 3) — a coleta de localização precisa
Quando vira chamado, o bot conduz a **captura de localização robusta** (ver §5.1):
```
Bot: Estamos com você. Toque no clipe 📎 → Localização → "Localização atual"
     (e deixe "tempo real" ligado se puder).
Bot: Onde você está agora?
  🏠 Dentro de casa, térreo
  🪜 Andar de cima / laje
  🏔️ No telhado
  🚗 Em cima de um carro / muro
  🌊 Na água / sendo levado(a)
Bot: Quantas pessoas com você? Tem criança, idoso ou alguém ferido?
Bot: A água está: parada / subindo devagar / subindo rápido?
```
Cada resposta alimenta a **priorização**. Mensagens curtas, botões > texto livre (digitar é difícil em pânico/molhado).

### 4.4 PWA de campo — fluxo da equipe de resgate
- Login por link assinado (sem app store, sem senha digitada).
- Tela única: **lista dos meus chamados** ordenada por proximidade + prioridade.
- Botão **"Assumir"** → coloca lock no chamado (ninguém mais pega) → abre navegação (Google/Waze/coordenada).
- Botões grandes de status: **A caminho → No local → Resgatado (quantas pessoas) → Levado ao abrigo X**.
- Funciona offline: ações enfileiram e sincronizam quando a conexão volta.

### 4.5 Reunificação familiar
```
Bot (canal público): Procurando alguém? Me diga nome e último local conhecido.
→ cria registro "procurado" → cruza com cadastros, check-ins de abrigo e resgates.
→ quando há match, notifica ambos os lados (respeitando consentimento/LGPD).
```

---

## 5. O coração tecnológico (o que de fato salva vidas)

### 5.1 Localização precisa — quando o endereço não serve
Camadas combinadas, da melhor pra pior:

1. **GPS ao vivo** via token-link (PWA com `watchPosition`, alta acurácia). Transmite continuamente enquanto a aba fica aberta.
2. **Localização do WhatsApp** (pin único e "tempo real" de 15 min — nativo, funciona sem abrir link).
3. **what3words / Open Location Code (Plus Codes)** — endereço de 3m² que a equipe de campo lê e digita no GPS mesmo offline. Crítico em área sem nome de rua útil.
4. **Altimetria/contexto vertical** — térreo / andar / **telhado** (definido por botão na §4.3). Muda o tipo de equipe (barco x helicóptero x escada).
5. **Foto georreferenciada** — vítima manda foto; EXIF + visão computacional confirma cenário (água, telhado, nº de pessoas).
6. **Triangulação aproximada** (último recurso) — célula/IP quando nada acima existe; marca como "baixa precisão" no mapa.

Cada ponto carrega **acurácia (raio em metros)** e **timestamp**, e o mapa mostra isso (círculo de incerteza) pra equipe não confiar cegamente.

### 5.2 Anti-duplicação & despacho (o moat do RS)
A dor #1 de 2024. Mecânica:

- **Clustering geográfico**: chamados dentro de ~30m + janela de tempo são agrupados como **possível duplicata** e mostrados juntos (a sala funde ou separa).
- **Dedup por telefone e por household**: mesma pessoa pedindo por 2 canais = 1 chamado.
- **Lock de atendimento**: um chamado em estado `assumido` fica travado para uma equipe; os demais veem "já tem equipe a caminho".
- **Estado canônico** por chamado: `aguardando → triado → despachado → assumido → no_local → resgatado → em_abrigo → encerrado` (+ `cancelado/duplicado/perdido_contato`).
- **Baixa por confirmação dupla**: equipe marca "resgatado" **e** o sistema tenta confirmar com a vítima ("você está segura agora?"). Evita o caso de 2024 (resgatado seguia na lista).
- **Despacho assistido**: a sala vê, pra cada chamado, as equipes livres mais próximas com ETA estimado e capacidade (barco 4 lugares, etc).

### 5.3 Resiliência de conectividade (continuar de pé quando a internet cai)
- **Payload mínimo**: priorizar texto/botão; só puxar mídia quando há banda.
- **Buffer offline no PWA da vítima e da equipe**: posições e ações ficam em fila local (IndexedDB) e retransmitem ao reconectar.
- **SMS fallback**: se a vítima não tem dados, mas tem sinal de voz/SMS, alerta e confirmação por SMS (gateway Zenvia/Twilio).
- **Ponte satélite (Starlink)**: a Sala de Comando e os pontos de apoio rodam atrás de Starlink; documentar como requisito operacional (em 2024 foi o que manteve comunicação de pé).
- **Degradação graciosa**: a Sala continua usável com dados defasados e marca claramente "última atualização há X min" por ponto.
- **Multi-AZ + fila durável** no backend pra não perder SOS sob pico de carga.

### 5.4 Mapa de comando — camadas
- 🔴 **Resgate** (aguardando/em rota) — clusterizado por bairro no zoom-out.
- 🟡 **Desconhecido** (sem resposta ao broadcast).
- 🟢 **OK** / 🔵 **Evacuado**.
- 🚤 **Frota** ao vivo (equipes de campo com posição e status).
- 🌊 **Mancha de inundação** prevista/observada (geofence + nível de rio).
- 🏠 **Abrigos** com vagas (verde = vaga, vermelho = lotado, 🐾 = pet).
- ⛔ **Vias bloqueadas/alagadas** (alimentadas pela própria frota que reporta).
- Heatmap de densidade de pedidos pra alocar recursos.
- Stack: **MapLibre GL** (sem lock-in/custo Mapbox) + tiles próprios/OSM; realtime via Supabase `postgres_changes`.

### 5.5 Triagem por IA + vulnerabilidade clínica
- **Classificador** (LLM barato tipo Haiku/GPT-4o-mini) lê texto/áudio transcrito/foto e devolve: gravidade (1–5), nº de pessoas, presença de criança/idoso/ferido, "na água" vs "telhado", água subindo rápido.
- **Score de prioridade** = gravidade × vulnerabilidade cadastrada × velocidade da água × tempo na fila. Empurra acamado/O₂/criança pro topo.
- **Sempre com humano no loop**: IA ordena a fila e sugere, operador decide. Audit registra a sugestão e a decisão.
- **Anti-falso-positivo**: confirmação ("você quis pedir socorro?") antes de mobilizar equipe, com threshold alto.

### 5.6 Integração hidrológica & gatilhos
- Ingestão periódica de CEMADEN, ANA/SGB, INMET/MetSul, régua do Guaíba.
- **Regras de gatilho** por município (cota/chuva acumulada/nível de alerta) → arma evento + sugere geofence de evacuação.
- Modelo simples de **mancha de inundação** por cota (cruzando cota prevista × MDT/topografia) pra estimar "quem vai alagar nas próximas Nh" — começa simplificado (curva cota×área conhecida do município) e evolui.

### 5.7 Integração com órgãos de resposta
- **190 (PM) / 193 (Bombeiros) / 192 (SAMU)**: começar com handoff operacional (a sala liga/encaminha com ficha pronta — coordenada, nº de pessoas, vulnerabilidade); evoluir pra integração via API onde o órgão permitir.
- **Defesa Civil municipal/estadual**: o sistema é a ferramenta deles; selo institucional via Defesa Civil estadual (RS tem estrutura ativa pós-2024).

---

## 6. Arquitetura técnica

### 6.1 Stack
- **Backend**: FastAPI (Python) + Redis (fila com prioridade) + Supabase (Postgres + Realtime + Storage + Auth).
- **Worker**: Python standalone, **modular** (`worker_defesa_civil.py`) — máquina de estados do chamado. (Não repetir o monólito de 900 linhas de Maringá.)
- **Frontend Sala**: Vite + React + TypeScript + Tailwind + **MapLibre GL**.
- **PWA vítima** e **PWA campo**: páginas leves, offline-first (Service Worker + IndexedDB).
- **Bot**: **WhatsApp Cloud API** (Meta) via camada de mensageria abstrata.
- **Infra**: multi-AZ; SLA-alvo 99.9%. (Coolify/Fly/Railway no piloto; endurecer pra produção.)

### 6.2 Multi-tenant
Uma instância serve N municípios. Isolamento por `tenant_id` (RLS no Supabase). Geofences, equipes, abrigos e cadastros são por tenant; relatórios agregados por município e por estado.

### 6.3 Camada de mensageria plugável
```
            ┌────────────────────────┐
  fluxo →   │   bot core (estados)   │
            └───────────┬────────────┘
                        │  envia/recebe (interface única)
        ┌───────────────┼───────────────┬──────────────┐
   WhatsApp Cloud    Evolution         SMS           Satélite/
   (produção)        (piloto)        (fallback)      Starlink (infra)
```
O core não sabe qual canal está embaixo — troca sem reescrever o fluxo. Fallback automático por disponibilidade/feature.

### 6.4 Realtime
Supabase `postgres_changes` → Sala e dashboards atualizam sem refresh. Mudança de estado de chamado, nova posição GPS, novo chamado, vaga de abrigo: tudo empurrado.

---

## 7. Modelo de dados (núcleo, focado Defesa Civil)

```
tenants                  (município/órgão)
geofences                (polígonos de área de risco; tipo: alagamento/deslizamento)
pessoas_protegidas       tel, nome, endereço, lat/lng, household_size,
                         vulnerabilidades[] (acamado/O2/dialise/idoso/crianca/cadeirante),
                         tem_pets, contato_confianca, geofence_id, tenant_id, campos_sensiveis(AES-256)
eventos                  (uma enchente/operação) — gatilho, geofence_impacto, início/fim
broadcasts               evento_id, template, geofence, enviados/entregues/respondidos
chamados_resgate         pessoa_id?, evento_id, origem(broadcast/foto/link/3p),
                         estado, prioridade_score, gravidade_ia, contexto_vertical(telhado/agua/...),
                         num_pessoas, dup_de(chamado_id?), tenant_id
rastreamento_sessoes     chamado_id, token único assinado
rastreamento_pontos      sessao_id, lat, lng, acuracia_m, fonte(gps/w3w/cell), ts
equipes_campo            nome, tipo(bombeiro/brigada/voluntario), capacidade, status, posição_atual
despachos                chamado_id, equipe_id, estado, ts_assumido, ts_no_local, ts_resgatado
abrigos                  nome, lat/lng, capacidade, ocupacao, pet_friendly, tem_medico, tenant_id
abrigo_checkins          abrigo_id, pessoa(nome/tel), chamado_id?, ts
reunificacao             quem_procura, procurado(nome/desc/ult_local), status, match_id?
vias_bloqueadas          geom, motivo, reportado_por(equipe_id), ts
eventos_audit            ator, acao, alvo, ts  (LGPD — quem viu/fez o quê)
```

Reaproveita de Maringá (com ajuste): `rastreamento_sessoes`/`rastreamento_pontos` ≈ `emergencia_*`; token-link da página da vítima.

---

## 8. Privacidade, LGPD & segurança
- **Base legal**: proteção da vida (interesse vital) + execução de política pública por órgão competente.
- **Dados sensíveis** (saúde/vulnerabilidade, localização): **AES-256 em repouso** nos campos sensíveis; acesso por papel; tudo em `eventos_audit`.
- **Minimização**: coletar só o que prioriza resgate. Retenção definida; expurgo pós-evento dos dados não necessários.
- **Consentimento** no cadastro prévio; na emergência prevalece o interesse vital.
- **Token-link assinado** e expirável; reunificação só revela dados com consentimento dos dois lados.
- Caminho **ISO 27001** + DPO conforme o doc fundador.

---

## 9. Métricas (recorte Defesa Civil)
- **Tempo broadcast → 1ª resposta** da população.
- **Tempo SOS → equipe assumir** (alvo < 60s na sala) e **SOS → resgate concluído**.
- **% cobertura GPS** dos chamados (alvo > 90%).
- **Taxa de duplicatas detectadas/evitadas** (KPI próprio do RS).
- **% de vulneráveis cadastrados evacuados preventivamente** (a métrica que mais salva vida).
- **Vidas atendidas no evento** — métrica-mor, documentável caso a caso.

---

## 10. Roadmap de MVP (recorte RS, ~3 meses)

**Mês 1 — Núcleo**
1. Schema Supabase (§7) + multi-tenant + RLS.
2. Webhook WhatsApp Cloud API + camada de mensageria.
3. Cadastro prévio de morador via bot (§4.1).
4. Token-link PWA de rastreamento (offline-first).

**Mês 2 — Operação**
5. Sala de Comando: mapa MapLibre + fila por prioridade + realtime.
6. Broadcast por geofence + triagem 1/2/3 (§4.2).
7. Máquina de estados do chamado + anti-duplicação + lock de despacho (§5.2).
8. PWA de campo da equipe de resgate (§4.4).

**Mês 3 — Piloto real no RS**
9. Abrigos + check-in; reunificação básica.
10. Ingestão hidrológica (CEMADEN/régua) + gatilho de evento.
11. SMS fallback; requisito Starlink documentado.
12. Piloto com 1 município (Vale do Taquari / Região Metropolitana POA / serra) na estação chuvosa; coletar caso real.

**Fora do MVP**: app mobile dedicado, integração API direta com viatura, IA preditiva avançada de mancha, wearables.

---

## 11. Riscos específicos do RS

| Risco | Mitigação |
|---|---|
| Internet cai no pico (torres alagadas) | Offline-first, SMS, Starlink na sala, payload leve, fila durável |
| Volume de broadcast → ban/limite WhatsApp | Cloud API oficial + templates pré-aprovados + rate-limit + Telegram/SMS backup |
| Município sem operador 24/7 na crise | "Sala de Comando como Serviço" (operadores próprios de plantão) |
| Voluntários não-treinados na frota | PWA de campo idiot-proof (botões grandes) + onboarding de 2 min + verificação de identidade |
| Localização imprecisa leva equipe ao lugar errado | Múltiplas fontes + raio de incerteza explícito + what3words pra leitura humana |
| Falso positivo mobiliza recurso escasso | Confirmação + threshold alto + humano no loop |
| Dados sensíveis vazam | AES-256, RLS, audit, minimização, expurgo |

---

## 12. Decisões em aberto (Defesa Civil)
1. **Origem dos dados hidrológicos** — quais APIs/feeds do RS priorizar primeiro (CEMADEN vs régua municipal vs ANA)?
2. **Modelo de frota** — só equipes oficiais (bombeiro/Defesa Civil) ou incluir voluntários cadastrados desde o MVP?
3. **Município-piloto** — Vale do Taquari (rio), Região Metropolitana POA (urbano/diques) ou serra (deslizamento)? Cada um estressa o sistema de um jeito.
4. **Sala como serviço** vs cliente opera — define carga operacional e margem.
5. **what3words** (licença) vs **Plus Codes** (aberto/grátis) pra endereçamento de 3m².

---

## 13. Rastreamento com o app FECHADO — investigação técnica

**Pergunta:** quando a vítima manda a localização e **fecha o PWA**, dá para continuar recebendo o GPS em tempo real?

**Veredito honesto:** com **web pura (PWA), não.** É uma barreira de plataforma, intencional, por privacidade — não um bug que se contorna.

### Por que a web não resolve
- **Service Worker não tem acesso à Geolocation API.** Mesmo com *Periodic Background Sync*, o SW não consegue ler GPS; no máximo acorda e manda mensagem a uma aba **já aberta**. Frequência atrelada ao engajamento e intervalos longos (inúteis para emergência).
- **iOS Safari**: rastreamento em background com app fechado **não é viável** — é o maior gap entre PWA e nativo no iPhone. *Background Sync* nem é suportado.
- `watchPosition()` só roda com a página em foreground; ao fechar a aba, o JS para.

### O que dá para fazer em web pura (já implementado no `pwa-vitima`)
1. **Wake Lock API** — mantém a tela acesa para o aparelho não suspender o GPS enquanto aberto. Reaquisição automática ao voltar o foco.
2. **Buffer offline + retransmissão** — não perde posições quando o sinal cai.
3. **Último ponto conhecido sempre vale** — com timestamp + raio de incerteza. Numa enchente a vítima quase não se desloca (telhado), então o último ponto costuma bastar para o resgate.
4. *(a fazer)* **Reativação por Web Push** — quando o sinal some por X s, servidor manda push; a pessoa toca e o PWA reabre, retomando a transmissão. Semi-automático.

### A solução real para "app fechado": camada nativa (fase futura)
Empacotar o mesmo web app com **Capacitor** + plugin **`@capacitor-community/background-geolocation`** (ou Transistorsoft):
- **Android**: *foreground service* tipo `location` + notificação persistente; com `stopOnTerminate:false` transmite **mesmo com o app encerrado** (modo headless). Permissões `ACCESS_FINE_LOCATION` + `ACCESS_BACKGROUND_LOCATION` + `FOREGROUND_SERVICE`.
- **iOS**: `UIBackgroundModes: location` + `NSLocationAlwaysAndWhenInUseUsageDescription`; updates não param por inatividade.
- Suporta **só iOS/Android** e exige **instalar um app** → quebra a tese de "zero instalação".

### Recomendação: modelo de duas camadas
- **Camada A (massa, zero instalação):** PWA token-link com Wake Lock + offline + último-ponto. Cobre o evento de massa sem fricção. É o padrão.
- **Camada B (opcional, alto risco):** app nativo (Capacitor) **oferecido a vulneráveis pré-cadastrados** (acamado, O₂, idoso só) que aceitam instalar e dar permissão "sempre". Rastreamento contínuo confiável para quem mais precisa. Reaproveita ~100% do código web.

Fontes: [MDN — Offline & background](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Offline_and_background_operation), [MDN — Periodic Background Sync](https://developer.mozilla.org/en-US/docs/Web/API/Web_Periodic_Background_Synchronization_API), [PWA iOS Limitations 2026](https://www.magicbell.com/blog/pwa-ios-limitations-safari-support-complete-guide), [capacitor-community/background-geolocation](https://github.com/capacitor-community/background-geolocation).

---

*Documento vivo. Recorte: Defesa Civil RS. §10 já materializado em `sos-vision-defesa-civil/` (MVP executável). Próximos candidatos: camada nativa de rastreamento (§13), embelezar Sala/mapa (fase 2), broadcast real WhatsApp + ingestão hidrológica.*
