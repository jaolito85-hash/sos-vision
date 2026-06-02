# Plataforma de Telemetria Humana via WhatsApp
## Documento Fundador · Maio/2026

> Este documento é o brief executivo + spec inicial para fundar um novo produto, derivado da experiência do projeto Maringá (Node Data — Central de Segurança Pública) mas independente em código, marca, banco e infraestrutura.

---

## 1. Tese do produto

### O insight central

> **O celular que toda vítima já tem é um beacon de socorro inativo. O WhatsApp é o app que ela já abre 6h por dia. Falta a ponte entre os dois e uma sala de comando do outro lado.**

O concorrente real do produto **não é outro app de pânico** — é o "liga 190 e torce", que ainda é o padrão hoje em 95% das emergências individuais no Brasil.

### O ativo técnico raro (o moat)

Cinco propriedades combinadas que big tech não entrega:

1. **Zero atrito de instalação** — usa o WhatsApp que já está na tela inicial.
2. **GPS em tempo real de uma vítima qualquer em < 30s**, sem instalar nada (token-link assinado).
3. **Canal humano bidirecional** — IA classifica + operador assume + voz volta pra cidadão.
4. **Cadastro prévio de pessoa vulnerável** — contatos de confiança, foto do agressor, endereços, riscos clínicos.
5. **Sala de comando realtime** — mapa, fila por prioridade, audit LGPD, protocolo rastreável.

Apple/Google dependem de SDK, conta na loja, autorização nativa de background-location. Nós contornamos isso usando **WhatsApp como sistema operacional do socorro**. Esse é o moat.

### Posicionamento de marca

**Não é "app de pânico". É _Sistema Operacional de Proteção Cidadã_.**

Tagline candidata: *"Toda emergência tem coordenadas. Nós encontramos."*

---

## 2. As 10 verticais (priorizadas por receita / esforço)

### 🌊 V1. Defesa Civil — alagamento, deslizamento, vendaval **(VETOR PRIMÁRIO)**

**Cenário:** Petrópolis 2022 (235 mortos), Recife 2022 (133), São Sebastião 2023 (65). Todos com celular no bolso.

**Mecânica:**
- Cadastro prévio dos moradores em áreas de risco (Defesa Civil já tem o mapa).
- Quando alerta meteorológico dispara: bot envia mensagem em massa → *"Chuva forte chegando. Você está bem? Responda 1 (em casa), 2 (fora), 3 (preciso de ajuda)"*.
- Quem não responde em X min vira "status desconhecido" no painel.
- Quem responde 3 → SOS imediato com link de rastreamento.
- Quem manda foto/vídeo → IA classifica gravidade, prioriza fila de resgate.
- Bot envia rota de fuga personalizada baseada em modelo hidrológico ("saia pelos fundos, suba a Rua X").
- Sala vê mapa de calor: amarelo (sem resposta), verde (ok), vermelho (resgate).

**Por que prioridade #1:**
- Defesa Civil tem orçamento federal (PNUDEM, Funcap) e estadual.
- Mercado desértico — todos os "apps de defesa civil" hoje só notificam, nenhum faz telemetria.
- Demanda explode pós-tragédia (a próxima estação chuvosa garante leads).
- Mudança climática só piora o problema (TAM crescente).

**Tíquete estimado:** R$ 250k–800k/ano por município médio.

---

### 🛡️ V2. SOS Mulher

**Cenário:** Lei Maria da Penha + Decreto Cidadão Ativo. Já é o produto referência de Maringá.

**Mecânica:** vítima cadastrada com agressor, contato de confiança, endereço; aciona via código discreto ou tap em link salvo; rastreamento ao vivo até resgate.

**Por que está em segundo lugar:** mercado mais saturado (Salve Maria de SP, Mulher Segura PR, apps estaduais). Competir aqui exige diferencial (preço + integração com viatura PM via API + IA de risco preditivo).

**Tíquete:** R$ 150k–500k/ano por município.

---

### 🚨 V3. Criança Localizada — Alerta Amber municipal

**Mecânica:**
- Pais cadastram filho com foto + dados (escola, rotina).
- Sumiço dispara protocolo: bot envia broadcast pra cidadãos cadastrados num raio de 5 km com a foto da criança.
- Cidadão que vê responde com foto + localização.
- Polícia vê mapa de avistamentos consolidado em tempo real.

**Hoje:** isso é feito via Twitter/Instagram amador. Existe demanda institucional, sem produto.

**Tíquete:** R$ 80k–250k/ano por município.

---

### 👴 V4. Idoso Protegido

**Mecânica:** filho cadastra mãe/pai com riscos clínicos (cardíaco, Alzheimer, Parkinson). Idoso abre conversa salva no WhatsApp e manda "passei mal" / "me perdi". SAMU + filho + vizinho de confiança recebem ao mesmo tempo, com GPS ao vivo.

**Extensão futura:** pulseira BLE simples envia via celular (sem necessidade do idoso abrir WhatsApp).

**Tíquete:** B2G (R$ 100k–300k/ano por convênio com Secretaria de Saúde) + B2C (R$ 19,90/mês família).

---

### 🚚 V5. Trabalhador em Risco

**Cliente:** logística (motoboys, transporte de cargas), segurança privada, agentes comunitários de saúde, fiscais ambientais, motoristas de aplicativo.

**Mecânica:** botão de pânico no WhatsApp aciona alerta com GPS. Sala da empresa/cooperativa atende.

**B2B puro.** Tíquete: R$ 8–15/usuário/mês × 1000+ usuários = R$ 100k–200k/mês por conta corporativa grande.

---

### 🩺 V6. Visita Domiciliar Segura

**Cliente:** Secretarias de Saúde (ACS), assistentes sociais, técnicos de instalação (gás, internet).

**Mecânica:** check-in ao chegar na visita, check-out ao sair. Se passa do tempo previsto sem check-out → trigger automático.

**Tíquete:** R$ 80k–250k/ano por município (cobre milhares de agentes).

---

### ⛰️ V7. Turismo Seguro / Aventura

**Cliente:** Parques Nacionais, operadoras de trilha, ICMBio, secretarias de turismo.

**Mecânica:** trilheiro cadastrado na portaria do parque. Não voltou no horário esperado → busca automatizada com última posição GPS.

**Tíquete:** R$ 30–80 por turista/excursão (B2B operadora) ou R$ 50k/ano por parque (B2G).

---

### 🏥 V8. Pacientes em Surto / CAPS

**Cliente:** CAPS municipais, hospitais psiquiátricos, casas de acolhimento.

**Mecânica:** monitoramento opcional de pacientes que costumam fugir (com consentimento legal/familiar).

**Mercado pequeno mas estável.** Tíquete: R$ 50k–150k/ano por rede.

---

### 🎉 V9. Eventos Massivos

**Cliente:** organizadores de shows, jogos, carnaval, manifestações grandes.

**Mecânica:** voluntários e brigadistas cadastrados temporariamente. Painel mostra hotspots de tumulto, agressão, problema médico.

**Receita por evento:** R$ 30k–200k pontual.

---

### 🌍 V10. Defensores de Direitos / Jornalistas / Indígenas

**Cliente:** ONGs (Anistia, ARTIGO 19, ISA), Funai, Ministério Público.

**Mecânica:** proteção contínua de pessoas em conflito territorial. Botão de pânico + GPS + chamada de rede.

**Receita:** doação institucional + selo de impacto (não foco comercial, mas ótimo pra branding).

---

## 3. Modelos de receita

### 🅰️ B2G — onde está o dinheiro grande

| Cliente | Vertical | Tíquete anual |
|---|---|---|
| Município pequeno (≤100k hab) | 1 vertical | R$ 80k–250k |
| Município médio (100k–500k) | Pacote 2 verticais | R$ 250k–800k |
| Capital / metrópole | Pacote 5 verticais | R$ 1.5M–6M |
| Governo estadual | Camada estadual + integração 190/193 | R$ 5M–20M |
| Federal (Casa Civil, MMFDH, Defesa Civil Nacional) | SaaS federal | R$ 20M–80M |

**Estratégia comercial:** vender modular por vertical. *"Compra Defesa Civil agora, expande SOS Mulher em 12 meses."* Reduz fricção do procurement e amplia ARPU ao longo do tempo (land-and-expand).

### 🅱️ B2B — escala mais rápida

| Cliente | Caso | Modelo |
|---|---|---|
| Logística / motofretes | Pânico do entregador | R$ 8–15/usuário/mês |
| Apps mobilidade (Uber, 99, iFood) | API de pânico passageiro/entregador | Por evento + setup |
| Operadoras turismo | Rastreamento de grupos | R$ 30–80/turista/excursão |
| Universidades | Segurança no campus | R$ 2–5/aluno/ano |
| Imobiliárias / corretoras | Corretor em visita | R$ 50/corretor/mês |
| Seguradoras | Add-on de plano residencial / vida | Receita compartilhada |

### 🅲 B2C — receita longa

App freemium familiar — **R$ 19,90/mês cobre 5 pessoas** (ex: mãe idosa + 3 filhos + esposa). Gateway pra famílias entrarem antes da prefeitura assinar.

### 🅳 Receitas auxiliares

- **Treinamento de operadores** municipais — R$ 5k–15k por turma.
- **Integração com câmeras inteligentes** (Smart City Hub) — venda cruzada.
- **Dados agregados anônimos** pra seguradoras e pesquisa (com cuidado LGPD).
- **Certificação ISO 27001 + LGPD** — selo que justifica preço maior.

---

## 4. Estratégia Go-to-Market (12-18 meses)

### Fase 1 — M1 a M3: Lock-in Maringá + Case
- Fechar contrato Maringá e operar em produção real.
- **Capturar 3 vidas reais salvas** com depoimento em vídeo de 90s — vira a arma de vendas mais poderosa que existe.
- Métrica do prefeito: *"redução de tempo médio de resposta de 12 min para 90s"*.

### Fase 2 — M3 a M9: Vetor Defesa Civil
- **Não vai com SOS Mulher primeiro.** Mercado saturado, big tech briga.
- Atacar **Defesa Civil**: mercado desértico, orçamento federal, demanda crescendo com mudança climática.
- **Cidades pós-tragédia** com prefeito traumatizado e orçamento aberto:
  - Petrópolis, Nova Friburgo, Teresópolis (Serrana RJ)
  - Recife, Paulista, Olinda, Jaboatão (PE)
  - São Sebastião, Bertioga, Caraguatatuba (Litoral SP)
  - Blumenau, Brusque (SC)
- **Aliar com Defesa Civil Nacional** pra ganhar selo institucional.

### Fase 3 — M9 a M18: Plataforma multi-vertical
- Maringá vira referência regional → tração no Paraná todo.
- Empacotar IP: **"Telemetria Humana via WhatsApp"** — registrar marca, gerar white paper técnico.
- Buscar concessão estadual (PR, SP, MG são alvos óbvios).
- Levantar Series Seed/A se quiser acelerar (pitch: SaaS govtech crítico, 10 verticais, moat tecnológico real).

---

## 5. Arquitetura reaproveitável de Maringá

### O que portar (conceitos, não código)

**Schema de dados centrais:**
- `pessoas_protegidas` (refinamento de `sos_cadastros`) — telefone, nome, endereço, foto, riscos clínicos, contatos de confiança, agressores conhecidos
- `protecao_alertas` (refinamento de `sos_alertas`) — vincula pessoa, status (active/attending/resolved), token de rastreamento, vertical (mulher/defesa-civil/idoso/etc), timestamps
- `rastreamento_sessoes` (igual `emergencia_sessoes`) — token único por alerta
- `rastreamento_pontos` (igual `emergencia_pontos`) — GPS contínuo, schema preservado
- `eventos_audit` — LGPD (quem viu o quê, quando)

**Componentes técnicos comprovados:**
- Webhook WhatsApp (Evolution API) com classificação IA (GPT-4o-mini) — manter
- Fila Redis com prioridade — manter
- Worker process — refatorar do zero (worker.py de Maringá tem 900 linhas, dívida técnica)
- Token-link de rastreamento via página estática (`mulher-segura.html`) — preservar mas modernizar pra PWA
- Realtime via Supabase postgres_changes — manter
- Sala de comando (dashboard React + Mapbox) — refatorar (não trazer o monólito HTML)

### O que cortar do projeto atual

- Denúncias, ocorrências, recompensas, feedback, arborização, radar de notícias — **fora**. Esse novo produto é só proteção pessoal.
- Frontend monolítico em HTML+CDN — usar Vite + React real, componentes em arquivos separados.
- Worker gigante — quebrar por vertical (worker_defesa_civil.py, worker_sos_mulher.py).

### O que precisa ser novo

- **Sistema multi-tenant** — uma instância serve N municípios e N empresas (diferente de Maringá, que é single-tenant).
- **Multi-vertical** — engine que ativa fluxos diferentes por tipo de cliente/cadastro.
- **Broadcast em massa** (essencial pra Defesa Civil) — não existe em Maringá.
- **Dashboard de operadores** com perfis e permissões reais (Maringá é open).
- **API pública** documentada (B2B vai integrar com sistemas próprios).
- **App mobile** complementar pra família — opcional fase 2.

---

## 6. MVP do novo sistema (3 meses)

### Stack mínima
- Backend: FastAPI + Redis + Supabase (Postgres + Realtime + Storage)
- Worker: Python standalone, modular por vertical
- Frontend: Vite + React + TypeScript + Tailwind + Mapbox/MapLibre
- Bot: Evolution API ou WhatsApp Cloud API oficial (avaliar trade-off custo/risco)
- Auth: Supabase Auth (operadores) + Token-link assinado (vítimas)
- Infra: Coolify ou Fly.io ou Railway (decidir)

### Funcionalidades obrigatórias do MVP
1. Cadastro de pessoa protegida (via WhatsApp guiado por bot)
2. Disparo de SOS via código de palavra
3. Token-link de rastreamento (página estática, sem app)
4. Sala de comando realtime com mapa + fila
5. Aceitar/atender/resolver com audit
6. Notificação push pro operador (Slack/Telegram/email)
7. Multi-tenant por município/empresa
8. **Vertical Defesa Civil**: cadastro de área de risco + broadcast em massa por geofence
9. **Vertical SOS Mulher**: igual Maringá

### Funcionalidades fora do MVP
- App mobile dedicado
- Integração com viaturas PM
- IA preditiva de risco
- Pulseiras/wearables
- Pagamentos B2C

---

## 7. Jornada da pessoa em risco (UX core)

### Pré-cadastro (proativo, antes da emergência)
1. Pessoa adiciona o número oficial no WhatsApp.
2. Bot apresenta opções: *"Olá, sou o Guardião. Quer se cadastrar para receber proteção em emergências?"*
3. Bot guia coleta: nome, endereço, foto (opcional), contato de confiança.
4. Conforme vertical, perguntas extras (Defesa Civil: bairro/área de risco; SOS Mulher: agressor + foto).
5. Token de proteção criado, pessoa recebe link "Toque em emergência" salvo nos contatos.

### Disparo (no momento da crise)
- **SOS Mulher:** envia palavra-código discreta ("preciso de uma pizza") OU toca link salvo.
- **Defesa Civil:** responde "3" ao broadcast OU envia foto da água subindo.
- **Idoso:** toca link "Estou mal" salvo.

### Atendimento
1. Sistema classifica + prioriza + alerta operador.
2. Operador na sala vê: dados da pessoa + mapa + trilha GPS (se vítima abriu o link).
3. Operador aceita atendimento, faz handoff humano (chat direto), aciona PM/SAMU/Bombeiro via API ou telefone integrado.
4. Cidadão recebe atualização *"equipe a 3 minutos"* via WhatsApp.
5. Sistema registra audit completo.

### Pós-evento
- Resolução + relatório automático.
- Acompanhamento (mensagem 24h depois: *"você está bem?"*).
- Estatística agregada pro gestor (mapa de calor, tempo médio, taxa de resolução).

---

## 8. Riscos e mitigações

| Risco | Severidade | Mitigação |
|---|---|---|
| **WhatsApp banir / mudar política da API** | Alto | Migrar pra WhatsApp Cloud API oficial (Meta Business). Mais caro mas com SLA. Ter Telegram como backup. |
| **LGPD — dados sensíveis (CPF, agressor, GPS)** | Alto | Criptografia AES-256 em campos sensíveis (já tem em Maringá). DPO contratado. ISO 27001 em 12 meses. |
| **False positives → cidadão recebe alarme falso** | Médio | Fluxo de confirmação ("você quis dizer SOS?") + IA bem treinada + threshold alto. |
| **Concorrência big tech (Google/Apple Find My)** | Médio | Foco em pessoa-específica + sala de comando + canal humano. Big tech não faz isso. |
| **Município não tem operador 24/7** | Alto | Oferecer "Sala de Comando como Serviço" — operadores próprios atendendo plantão. Receita extra. |
| **Falha de infra no momento crítico** | Crítico | Multi-AZ, fallback automático, monitoramento agressivo. SLA contratual de 99.9%. |
| **Vítima sem internet no momento do SOS** | Médio | Buffer local na página + retransmissão quando voltar. SMS como fallback. |

---

## 9. Métricas que importam

### Métricas de produto (operacionais)
- **Tempo médio entre disparo do SOS e operador aceitando** (alvo: < 30s)
- **Tempo entre disparo e equipe no local** (alvo: < 8 min)
- **Taxa de resolução positiva** (alvo: > 95%)
- **Taxa de falsos positivos** (alvo: < 5%)
- **Cobertura GPS** (% dos alertas que conseguiram capturar pelo menos 1 ponto GPS — alvo: > 90%)

### Métricas de negócio
- **MRR/ARR por vertical e por tipo de cliente**
- **Net Revenue Retention** — quanto cliente atual aumenta de vertical
- **CAC payback** (alvo B2G: < 18 meses)
- **NPS de operadores** (eles que usam diariamente, opinião deles dita renovação)

### Métrica-mor (a única que importa publicamente)
**Vidas salvas por mês.** Métrica simples, comprovável (cada caso documentado), poderosa em pitch e mídia. *"O sistema X salvou 47 vidas em janeiro."*

---

## 10. Próximos passos concretos

### Semana 1-2 — Validação e nome
- Definir nome do produto + domínio + marca registrada
- Pesquisar concorrentes diretos por vertical (mapa competitivo)
- Conversar com 5 prefeituras pós-tragédia (Petrópolis, Recife, São Sebastião) — descoberta

### Semana 3-4 — Repo zerado
- Criar repositório novo limpo (mono-repo: backend, worker, frontend, mobile-pwa)
- Setup Supabase novo (projeto separado de Maringá)
- Setup CI/CD desde o dia 1
- Schema mínimo (pessoas_protegidas, protecao_alertas, rastreamento_*)

### Mês 2 — MVP V1 (Defesa Civil)
- Cadastro de pessoa protegida via WhatsApp
- Cadastro de área de risco (operador desenha polígono no mapa)
- Broadcast em massa por geofence
- Sala de comando básica
- Token-link de rastreamento

### Mês 3 — Piloto real
- Pegar 1 prefeitura pequena disposta a piloto gratuito (3-6 meses)
- Treinar operadores
- Operar em estação chuvosa
- Coletar caso real
- Refinar produto baseado em uso

### Mês 4-6 — Comercialização
- Pricing definido
- Material de vendas (deck, white paper, vídeo de case)
- Equipe de vendas (1-2 pessoas focadas em B2G)
- Pipeline de 20 prefeituras

---

## 11. Diferencial competitivo defensável

### Por que isso não é commodity facilmente clonável

1. **Multi-vertical com engine compartilhada** — concorrente teria que construir 10 produtos. Nós temos 1 que vira 10.
2. **WhatsApp como interface** — exige integração não-trivial (Evolution + WhatsApp Cloud), conhecimento de webhook, dedup, classificação.
3. **Bot com IA contextual** — modelo de classificação por canal, etapas de sessão, handoff humano. Difícil de copiar sem dataset real.
4. **Rede de operadores treinados** — vai virar parte do produto (operação como serviço).
5. **Marca de "vidas salvas"** — confiança institucional não se compra rápido.

### Vantagens injustas
- Já tem case real rodando em Maringá → credibilidade desde o dia 1.
- Já tem código comprovado pra portar (não é greenfield total).
- Já tem entendimento profundo do problema → não vai gastar 6 meses em discovery.

---

## 12. Decisões que precisam ser tomadas agora

Pra fundar o produto novo, decisões pendentes:

1. **Nome e marca** — sugestões: *Guardião*, *Sentinela*, *Beacon*, *Salvar*, *NodeData SOS*.
2. **Estrutura societária** — empresa nova ou linha de produto da existente?
3. **WhatsApp API** — Evolution (mais barato, mais risco) vs Cloud API oficial (mais caro, com SLA Meta)?
4. **Tech stack frontend** — manter React (sabido) ou ir Next.js / outra coisa?
5. **Modelo de operadores** — só sistema (cliente opera) vs operação como serviço (mais margem, mais responsabilidade)?
6. **Onde levantar capital** — bootstrap até R$ 5M ARR vs Seed agora?

---

## Apêndice A — Glossário rápido

- **Vertical**: caso de uso específico (SOS Mulher, Defesa Civil, Idoso etc).
- **Token-link**: URL única assinada que rastreia GPS sem instalar app.
- **Broadcast geofence**: mensagem em massa pra todos os cadastrados dentro de um polígono geográfico.
- **Handoff humano**: momento em que o bot deixa de responder e operador assume a conversa.
- **Realtime**: via Supabase postgres_changes (WebSocket) — atualiza painel sem refresh.
- **B2G**: business-to-government (prefeituras, estados, federais).
- **B2B**: business-to-business (empresas).
- **B2C**: business-to-consumer (família paga assinatura).
- **ARPU**: average revenue per user.
- **MRR/ARR**: monthly/annual recurring revenue.

---

## Apêndice B — Recursos do projeto Maringá portáveis

**Pode ser reusado direto (com ajustes mínimos):**
- Migration `022_create_emergencia_tracking.sql` — schema do GPS
- Página `mulher-segura.html` — token-link da vítima (modernizar pra PWA)
- Página `monitor-sos.html` — visão de trilha (referência)
- Componente `SOSTrailMap` (recém-criado em `index.html` linha 2823) — Mapbox + Realtime
- Script `scripts/seed_sos_trilha.py` — base pra simulações de demo

**Conceitualmente reusável (reescrever do zero, mas com a lógica conhecida):**
- Webhook unificado (`backend/app/webhooks/unificado.py`) — fluxo de classificação IA
- Classificador (`backend/app/services/classificador.py`) — prompts e categorias
- Worker (`backend/worker.py`) — máquina de estados do SOS

**Não levar:**
- Frontend monolítico HTML+CDN (refazer como SPA real)
- Tabelas de denúncias, ocorrências, recompensas, feedbacks, arborização
- Rotas de API correspondentes

---

## Resumo em uma linha

> **Construir uma plataforma multi-vertical de telemetria humana via WhatsApp, começando por Defesa Civil, com Maringá (SOS Mulher) como case-âncora, com modelo B2G + B2B, alvo de R$ 5M ARR em 18 meses.**

---

*Documento vivo. Atualize conforme aprende. O que está aqui é a hipótese inicial, não a verdade absoluta.*
