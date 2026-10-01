# Teorema Fundamental de Curvas (Fundamental Theorem of Curves)
### Reconstrução de Curvas no $\mathbb{R}^3$, Integração de Frenet-Serret e Visualização Diferencial Interativa

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.24%2B-013243.svg?logo=numpy)](https://numpy.org/)
[![SciPy](https://img.shields.io/badge/SciPy-1.10%2B-8CAAE6.svg?logo=scipy)](https://scipy.org/)
[![SymPy](https://img.shields.io/badge/SymPy-1.12%2B-3B5526.svg?logo=sympy)](https://www.sympy.org/)
[![Plotly](https://img.shields.io/badge/Plotly-5.15%2B-3F4F75.svg?logo=plotly)](https://plotly.com/)
[![Tests](https://img.shields.io/badge/Tests-244%20passed-success.svg)](https://github.com/gabe-rbo/Teorema-Fundamental-de-Curvas)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Uma ferramenta computacional e acadêmica em Python que reconstrói curvas planas e espaciais a partir de suas funções intrínsecas de **curvatura** $\kappa(s)$ e **torção** $\tau(s)$ parametrizadas pelo comprimento de arco $s$. O sistema adota uma **arquitetura dual otimizada**:
- **Curvas Planas ($\tau(s) \equiv 0$):** Reconstruídas analiticamente via **Teorema Fundamental das Curvas Planas** por quadratura direta ($\theta(s) = \int \kappa(u)\,du$ e $r(s) = \int (\cos\theta, \sin\theta)\,du$) sem resolver EDOs tridimensionais, gerando visualização puramente em **2D cartesiano** com diedro de Frenet $\{T, N\}$, retas tangente e normal, e círculo osculador em escala 1:1.
- **Curvas Espaciais ($\tau(s) \not\equiv 0$):** Integradas numericamente pelo sistema diferencial de **Frenet-Serret** no grupo de Lie $\mathrm{SO}(3)$ com ortonormalização contínua de Gram-Schmidt, gerando cena **3D WebGL** com triedro $\{T, N, B\}$, planos osculador, normal e retificante, círculo osculador e vetor de Darboux.

Ambos os modos contam com classificação determinística em 8 famílias geométricas, interface web interativa em **Plotly HTML full-screen** (`100vw` $\times$ `100vh`), slider contínuo de navegação e suporte a clique na curva (`plotly_click`).

---

## Sumário
1. [Fundamentação Teórica](#fundamentação-teórica)
   - [Enunciado do Teorema Fundamental das Curvas Espaciais](#enunciado-do-teorema-fundamental-das-curvas-espaciais)
   - [Teorema Fundamental das Curvas Planas (Quadratura Direta)](#teorema-fundamental-das-curvas-planas-quadratura-direta)
   - [Sistema Diferencial de Frenet-Serret](#sistema-diferencial-de-frenet-serret)
   - [Formulação Matricial e Álgebra de Lie $\mathfrak{so}(3)$](#formulação-matricial-e-álgebra-de-lie-mathfrakso3)
   - [Vetor de Darboux e Rotação Instantânea](#vetor-de-darboux-e-rotação-instantânea)
   - [Aparato Diferencial: Planos Fundamentais e Círculo Osculador](#aparato-diferencial-planos-fundamentais-e-círculo-osculador)
   - [Referências Bibliográficas](#referências-bibliográficas)
2. [Instalação e Requisitos](#instalação-e-requisitos)
3. [Guia de Uso da Linha de Comando (CLI)](#guia-de-uso-da-linha-de-comando-cli)
   - [Tabela de Argumentos](#tabela-de-argumentos)
   - [Códigos de Saída (Exit Codes)](#códigos-de-saída-exit-codes)
   - [Nomenclatura Automática de Arquivos](#nomenclatura-automática-de-arquivos)
4. [Galeria das 8 Famílias de Curvas Suportadas](#galeria-das-8-famílias-de-curvas-suportadas)
   - [1. Reta](#1-reta-kappa--0-tau--0)
   - [2. Círculo](#2-círculo-kappa--textconst--0-tau--0)
   - [3. Hélice Circular](#3-hélice-circular-kappa--textconst--0-tau--textconst-ne-0)
   - [4. Hélice Cilíndrica Geral (Teorema de Lancret)](#4-hélice-cilíndrica-geral-teorema-de-lancret-tau--c-kappa)
   - [5. Espiral de Cornu / Clotoide](#5-espiral-de-cornu--clotoide-kappas--c-cdot-s-tau--0)
   - [6. Espiral Logarítmica](#6-espiral-logarítmica-kappas--frac1as--b-tau--0)
   - [7. Curva Plana Geral](#7-curva-plana-geral-tau-equiv-0)
   - [8. Curva Espacial Geral](#8-curva-espacial-geral-tau-not-equiv-0)
5. [Interface Interativa Dual (2D e 3D) e Recursos Visuais](#interface-interativa-dual-2d-e-3d-e-recursos-visuais)
   - [Visualização Puramente 2D para Curvas Planas ($\tau \equiv 0$)](#visualização-puramente-2d-para-curvas-planas-tau-equiv-0)
   - [Visualização 3D WebGL para Curvas Espaciais ($\tau \not\equiv 0$)](#visualização-3d-webgl-para-curvas-espaciais-tau-not-equiv-0)
   - [Layout Responsivo 100vw $\times$ 100vh](#layout-responsivo-100vw-times-100vh)
   - [Controle Deslizante (Slider) e Animação Seletiva](#controle-deslizante-slider-e-animação-seletiva)
   - [Navegação Click-to-Point (`plotly_click`)](#navegação-click-to-point-plotly_click)
   - [Cartão Flutuante HUD (Heads-Up Display)](#cartão-flutuante-hud-heads-up-display)
6. [Arquitetura de Software e Motor Matemático](#arquitetura-de-software-e-motor-matemático)
7. [Bateria de Testes Automatizados (244 Testes)](#bateria-de-testes-automatizados-244-testes)

---

## Fundamentação Teórica

### Enunciado do Teorema Fundamental das Curvas Espaciais

> **Teorema Fundamental da Teoria Local de Curvas no $\mathbb{R}^3$ (Existência e Unicidade):**
> Sejam $\kappa, \tau: [s_0, s_1] \to \mathbb{R}$ funções de classe $C^1$ (ou contínuas), tais que $\kappa(s) > 0$ para todo $s \in [s_0, s_1]$ (cf. **do Carmo**, 1976/2016, Seção 1-5; **Tenenblat**, 2008, Cap. 2; **Toponogov**, 2006, Seção 1.3; **Alencar, Santos & Frensel**, 2011, Cap. 2).
> 1. **Existência:** Existe uma curva parametrizada pelo comprimento de arco $r: [s_0, s_1] \to \mathbb{R}^3$ de classe $C^3$ cuja curvatura é $\kappa(s)$ e cuja torção é $\tau(s)$.
> 2. **Unicidade a Menos de Movimento Rígido:** Se $\tilde{r}: [s_0, s_1] \to \mathbb{R}^3$ for outra curva com as mesmas funções de curvatura e torção, então existe uma isometria euclidiana direta própria $M \in \mathrm{SE}(3)$ (composta por uma rotação $R \in \mathrm{SO}(3)$ e uma translação $v \in \mathbb{R}^3$) tal que:
>    $$\tilde{r}(s) = R \, r(s) + v, \quad \forall s \in [s_0, s_1].$$

Pelo Teorema de Picard-Lindelöf (ou Cauchy-Lipschitz), dado um referencial inicial ortonormal orientado positivamente $\{T(s_0), N(s_0), B(s_0)\} \in \mathrm{SO}(3)$ e um ponto inicial $r(s_0) = r_0 \in \mathbb{R}^3$, o problema de valor inicial linear possui solução única global em todo o intervalo $[s_0, s_1]$. No referencial canônico padrão adotado para curvas espaciais:
$$r(s_0) = (0, 0, 0)^T, \quad T(s_0) = (1, 0, 0)^T, \quad N(s_0) = (0, 1, 0)^T, \quad B(s_0) = (0, 0, 1)^T$$

### Teorema Fundamental das Curvas Planas (Quadratura Direta)

Para curvas no plano euclidiano $\mathbb{R}^2$, a torção é identicamente nula ($\tau(s) \equiv 0$), o que implica que a binormal é constante ($B(s) \equiv (0, 0, 1)^T$) e o movimento fica estritamente restrito ao plano gerado pelo diedro de Frenet $\{T(s), N(s)\}$.

> **Teorema Fundamental da Teoria Local de Curvas Planas (Existência e Unicidade):**
> Seja $\kappa: [s_0, s_1] \to \mathbb{R}$ uma função contínua arbitrária (a curvatura com sinal no plano, que pode ser positiva, nula ou negativa).
> 1. **Existência:** Existe uma curva plana parametrizada pelo comprimento de arco $r: [s_0, s_1] \to \mathbb{R}^2$ de classe $C^2$ cuja curvatura é $\kappa(s)$.
>    Com a condição canônica inicial $r(s_0) = (0, 0)^T$ e $T(s_0) = (1, 0)^T$ (ângulo $\theta_0 = 0$), o ângulo de inclinação da reta tangente $\theta(s)$ é obtido por **quadratura direta**:
>    $$\theta(s) = \theta_0 + \int_{s_0}^s \kappa(u)\,du$$
>    O referencial móvel planar (diedro ortonormal) é expresso imediatamente por:
>    $$T(s) = \begin{pmatrix} \cos \theta(s) \\ \sin \theta(s) \end{pmatrix}, \quad N(s) = \begin{pmatrix} -\sin \theta(s) \\ \cos \theta(s) \end{pmatrix}$$
>    E a trajetória da curva $r(s) = (x(s), y(s))$ resulta de uma segunda quadratura direta:
>    $$x(s) = \int_{s_0}^s \cos \theta(u)\,du, \quad y(s) = \int_{s_0}^s \sin \theta(u)\,du$$
> 2. **Unicidade a Menos de Movimento Rígido:** Se $\tilde{r}$ for outra curva plana com a mesma curvatura com sinal $\kappa(s)$, existe um movimento rígido próprio em $\mathrm{SE}(2)$ (rotação plana e translação) tal que $\tilde{r}(s) = R_\phi r(s) + v_0$.

**Eficiência e Precisão Numérica:**
Ao constatar $\tau \equiv 0$, o sistema **dispensa inteiramente** o integrador de EDOs tridimensional (`scipy.integrate.solve_ivp`). Em vez disso, aplica integração numérica por quadratura cumulativa de Simpson (`scipy.integrate.cumulative_simpson`) refinada com interpolação cúbica (`CubicSpline`). Isso reduz o tempo de computação para menos de 1 ms, mantém a ortonormalidade do diedro $\{T, N\}$ em nível de precisão de máquina ($|\|T\| - 1| < 10^{-15}, T \cdot N = 0$) e gera fechamento exato de círculos com erro $< 10^{-14}$.

### Sistema Diferencial de Frenet-Serret

O triedro móvel de Frenet é constituído pelos vetores unitários ortogonais:
- **Vetor Tangente Unitário:** $T(s) = \frac{dr}{ds}(s)$
- **Vetor Normal Principal:** $N(s) = \frac{1}{\kappa(s)} \frac{dT}{ds}(s)$
- **Vetor Binormal:** $B(s) = T(s) \times N(s)$

As taxas de variação desses vetores com respeito ao comprimento de arco $s$ satisfazem as célebres **Equações de Frenet-Serret** (**do Carmo**, 2016; **Tenenblat**, 2008):

$$\begin{aligned}
\frac{dr}{ds} &= T(s) \\
\frac{dT}{ds} &= \kappa(s) N(s) \\
\frac{dN}{ds} &= -\kappa(s) T(s) + \tau(s) B(s) \\
\frac{dB}{ds} &= -\tau(s) N(s)
\end{aligned}$$

Este sistema de 12 equações diferenciais ordinárias de primeira ordem acopladas (3 para a posição e 9 para as componentes dos vetores da base móvel) descreve a evolução cinemática e geométrica da curva no espaço tridimensional.

### Formulação Matricial e Álgebra de Lie $\mathfrak{so}(3)$

Denotando a matriz do referencial de Frenet como a matriz ortogonal $F(s) = [T(s) \mid N(s) \mid B(s)] \in \mathrm{SO}(3)$, a relação diferencial escreve-se compactamente como:

$$\frac{dF}{ds}(s) = F(s) \, \Omega(s)$$

onde $\Omega(s)$ é um elemento da álgebra de Lie $\mathfrak{so}(3)$ (o espaço das matrizes antissimétricas $3 \times 3$, $\Omega^T = -\Omega$):

$$\Omega(s) = \begin{pmatrix} 0 & -\kappa(s) & 0 \\ \kappa(s) & 0 & -\tau(s) \\ 0 & \tau(s) & 0 \end{pmatrix} \in \mathfrak{so}(3)$$

A antissimetria de $\Omega(s)$ garante analiticamente a conservação da ortonormalidade do triedro:

$$\frac{d}{ds} \left( F(s)^T F(s) \right) = \Omega(s)^T F(s)^T F(s) + F(s)^T F(s) \Omega(s) = -\Omega(s) + \Omega(s) = 0$$

Em integrações numéricas, acumulações de erro de ponto flutuante podem degradar a ortonormalidade ao longo de intervalos extensos. Para sanar essa perda, o motor deste projeto emprega um estágio de **Ortonormalização Modificada de Gram-Schmidt** com restauração exata da binormal pelo produto vetorial $B = T \times N$, garantindo $\det(F(s)) = +1$ e $\|T\| = \|N\| = \|B\| = 1$ com erro residual inferior a $10^{-9}$.

### Vetor de Darboux e Rotação Instantânea

A rotação instantânea do triedro de Frenet à medida que o referencial percorre a curva com velocidade unitária é descrita pelo **Vetor de Darboux** $\omega(s) \in \mathbb{R}^3$ (**Alencar, Santos & Frensel**, 2011; **do Carmo**, 1976/2016):

$$\omega(s) = \tau(s) T(s) + \kappa(s) B(s)$$

As equações de Frenet-Serret são expressas de forma unificada através do produto vetorial com o vetor de Darboux:

$$\frac{dT}{ds} = \omega(s) \times T(s), \quad \frac{dN}{ds} = \omega(s) \times N(s), \quad \frac{dB}{ds} = \omega(s) \times B(s)$$

A norma do vetor de Darboux $\|\omega(s)\| = \sqrt{\kappa(s)^2 + \tau(s)^2}$ representa a velocidade angular total do referencial de Frenet com respeito a $s$. O eixo instantâneo de rotação tem a direção de $\omega(s)$, e a razão $\tau(s)/\kappa(s)$ governa a inclinação desse eixo em relação ao plano osculador.

### Aparato Diferencial: Planos Fundamentais e Círculo Osculador

Para cada ponto $r(s)$ com $\kappa(s) > 0$, definem-se os seguintes elementos geométricos locais do aparato diferencial:

| Elemento | Vetor Normal | Equação do Plano / Conjunto | Significado Geométrico |
|---|:---:|:---:|---|
| **Plano Osculador** | $B(s)$ | $(X - r(s)) \cdot B(s) = 0$ | Plano que melhor aproxima a curva na vizinhança de $r(s)$ (ordem de contato $\ge 2$). Gerado por $\{T(s), N(s)\}$. |
| **Plano Normal** | $T(s)$ | $(X - r(s)) \cdot T(s) = 0$ | Plano ortogonal à direção de propagação $T(s)$. Gerado por $\{N(s), B(s)\}$. |
| **Plano Retificante** | $N(s)$ | $(X - r(s)) \cdot N(s) = 0$ | Plano ortogonal à aceleração normal. Contém a direção tangente $T(s)$ e a binormal $B(s)$. |
| **Reta Tangente** | — | $L_T(u) = r(s) + u \, T(s), \quad u \in \mathbb{R}$ | Direção infinitesimal de velocidade e deslocamento tangencial da curva. |
| **Círculo Osculador** | $B(s)$ | Centro $c(s) = r(s) + \rho(s) N(s)$, Raio $\rho(s) = \frac{1}{\|\kappa(s)\|}$ | Círculo no plano osculador com contato de **segunda ordem** com a curva em $r(s)$ (mesma posição $r(s)$, mesma tangente unitária $T(s)$ e mesma curvatura $\kappa(s)$). |


### Referências Bibliográficas

1. **Toponogov, V. A.** (2006). *Differential Geometry of Curves and Surfaces: A Concise Guide*. Birkhäuser, Boston. ISBN: 978-0-8176-4384-3.
2. **Tenenblat, K.** (2008). *Introdução à Geometria Diferencial*. Edgard Blücher / Editora UnB, 2ª edição. ISBN: 978-85-212-0457-2.
3. **Alencar, H., Santos, W., Frensel, K.** (2011). *Geometria Diferencial das Curvas*. IMPA (Instituto de Matemática Pura e Aplicada), Rio de Janeiro. ISBN: 978-85-244-0331-6.
4. **do Carmo, M. P.** (1976). *Differential Geometry of Curves and Surfaces*. Prentice-Hall (reedição revisada Dover Publications, 2016). ISBN: 978-0-486-80699-0.
5. **Lancret, M. A.** (1806). *Mémoire sur les courbes à double courbure*. Mémoires présentés à l'Institut d'Égypte / Mémoires des savants étrangers, t. I, Paris, pp. 416–454 (apresentado em 1802).

---

## Instalação e Requisitos

O projeto requer **Python 3.10 ou superior**.

### 1. Clonar o Repositório
```bash
git clone https://github.com/gabe-rbo/Teorema-Fundamental-de-Curvas.git
cd Teorema-Fundamental-de-Curvas
```

### 2. Criar e Ativar Ambiente Virtual
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou no Windows: .venv\Scripts\activate
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

---

## Guia de Uso da Linha de Comando (CLI)

O script executável `teorema-fundamental-curvas.py` oferece interface de linha de comando robusta, suportando tanto argumentos posicionais quanto flags explicitadas.

```bash
python3 teorema-fundamental-curvas.py <curvatura> [torcao] [opções]
```

### Tabela de Argumentos

| Argumento Posicional | Flag Curta | Flag Longa | Tipo | Padrão | Descrição |
|---|---|---|---|---|---|
| `curvatura` | `-k` | `--curvatura` | `str` | *Obrigatório* | Expressão matemática da curvatura $\kappa(s)$ em função de $s$ (e.g., `"1"`, `"s"`, `"1/(s+1)"`). |
| `torcao` | `-t` | `--torcao` | `str` | `"0"` | Expressão matemática da torção $\tau(s)$ em função de $s$ (e.g., `"1"`, `"0.5*s"`). |
| — | `-i` | `--intervalo` | `float float` | `0.0 6.28` | Intervalo do comprimento de arco $[s_0, s_1]$. Aceita constantes simbólicas como `pi`, `2*pi`, `-pi`. |
| — | `-n` | `--num-pontos` | `int` | `500` | Número de pontos de amostragem na discretização da curva ao longo do intervalo. |
| — | `-o` | `--output` | `str` | *Automático* | Caminho do arquivo HTML de saída. Se omitido, o nome é gerado automaticamente. |
| — | `-h` | `--help` | — | — | Exibe mensagem de ajuda com exemplos e encerra. |

### Códigos de Saída (Exit Codes)

| Código | Significado | Causa Típica |
|:---:|---|---|
| **0** | **Sucesso** | Reconstrução integrada, classificação calculada e arquivo HTML gerado com êxito. |
| **1** | **Erro Matemático / Validação** | Expressão fora da whitelist AST, divisão por zero, singularidade no domínio de integração, $\kappa(s) < 0$. |
| **2** | **Erro de Sintaxe na CLI** | Número incorreto de argumentos para `-i`, tipo numérico inválido para `-n`, argumentos desconhecidos. |

### Nomenclatura Automática de Arquivos

Quando a flag `-o / --output` não é fornecida, o motor gera um nome canônico e higienizado no formato:

```
<classe_da_curva>-k<curvatura_sanitizada>-t<torcao_sanitizada>-I<s0>_<s1>.html
```

Caracteres especiais são substituídos de forma segura para compatibilidade com todos os sistemas operacionais (e.g., `/` torna-se `_div_`, `*` torna-se `_mult_`, `^` torna-se `_pow_`).

---

## Galeria das 8 Famílias de Curvas Suportadas

O motor de classificação analisa simbolicamente e numericamente as funções $\kappa(s)$ e $\tau(s)$, identificando a família geométrica exata:

### Tabela de Classificação das 8 Famílias Geométricas

| # | Identificador (`classe`) | Condição de Curvatura $\kappa(s)$ | Condição de Torção $\tau(s)$ | Descrição Geométrica & Teorema | Exemplo de Execução CLI |
|:---:|---|---|---|---|---|
| 1 | `reta` | $\kappa(s) \equiv 0$ | $\tau(s) \equiv 0$ | Segmento linear geodésico no $\mathbb{R}^3$ | `"0"` `"0"` |
| 2 | `circulo` | $\kappa(s) \equiv c > 0$ | $\tau(s) \equiv 0$ | Circunferência planar de raio $R = 1/c$ | `"1"` `"0"` |
| 3 | `helice_circular` | $\kappa(s) \equiv c_1 > 0$ | $\tau(s) \equiv c_2 \neq 0$ | Hélice sobre cilindro circular reto | `"1"` `"1"` |
| 4 | `helice_cilindrica_geral` | $\kappa(s) > 0$ | $\frac{\tau(s)}{\kappa(s)} \equiv c \neq 0$ | Hélice cilíndrica geral (**Teorema de Lancret**, 1802) | `"1 + 0.1*sin(s)"` `"2*(1 + 0.1*sin(s))"` |
| 5 | `espiral_de_cornu` | $\kappa(s) = c \cdot s$ | $\tau(s) \equiv 0$ | Clotoide / Espiral de Euler-Cornu | `"s"` `"0"` |
| 6 | `espiral_logaritmica` | $\kappa(s) = \frac{1}{as+b}$ | $\tau(s) \equiv 0$ | Espiral logarítmica equiangular planar | `"1/(s + 1)"` `"0"` |
| 7 | `curva_plana` | $\kappa(s)$ arbitrária | $\tau(s) \equiv 0$ | Curva planar geral imersa em $\mathbb{R}^2$ | `"2 + sin(s)"` `"0"` |
| 8 | `curva_espacial` | $\kappa(s)$ arbitrária | $\tau(s) \not\equiv 0$ | Curva espacial tridimensional genérica | `"1 + 0.5*cos(s)"` `"0.5*s"` |


### 1. Reta ($\kappa = 0, \tau = 0$)
Quando a curvatura é identicamente nula, a curva não acelera transversalmente e reduz-se a um segmento linear ao longo do vetor tangente inicial.
```bash
python3 teorema-fundamental-curvas.py "0" "0" -i 0 10 -o reta.html
```
*Arquivo padrão gerado:* `reta-k0-t0-I0_10.html`

### 2. Círculo ($\kappa = \text{const} > 0, \tau = 0$)
Curvatura positiva constante e torção nula caracterizam um círculo planar de raio $R = 1/\kappa$. Com $\kappa = 1$, sobre $[0, 2\pi]$, a curva fecha-se com perímetro $2\pi$.
```bash
python3 teorema-fundamental-curvas.py "1" "0" -i 0 6.283185 -o circulo.html
```
*Arquivo padrão gerado:* `circulo-k1-t0-I0_6.28.html`

### 3. Hélice Circular ($\kappa = \text{const} > 0, \tau = \text{const} \ne 0$)
Curvatura e torção constantes e não nulas formam a hélice cilíndrica circular sobre um cilindro de raio $R = \frac{\kappa}{\kappa^2 + \tau^2}$ e passo $h = \frac{2\pi \tau}{\kappa^2 + \tau^2}$.
```bash
python3 teorema-fundamental-curvas.py "1" "1" -i 0 12.56 -o helice_circular.html
```
*Arquivo padrão gerado:* `helice_circular-k1-t1-I0_12.56.html`

### 4. Hélice Cilíndrica Geral / Teorema de Lancret ($\tau(s)/\kappa(s) = c$)
Pelo **Teorema de Lancret (1802)**, uma curva no espaço é uma hélice cilíndrica geral se e somente se as retas tangentes formam um ângulo constante $\alpha$ com uma direção fixa no espaço ($\tau(s)/\kappa(s) = \cot \alpha = \text{const}$).
```bash
python3 teorema-fundamental-curvas.py "1 + 0.1*sin(s)" "2*(1 + 0.1*sin(s))" -i 0 6.28
```
*Arquivo padrão gerado:* `helice_cilindrica_geral-k1_plus_0_1_mult_sin_s-t2_mult_1_plus_0_1_mult_sin_s-I0_6.28.html`

### 5. Espiral de Cornu / Clotoide ($\kappa(s) = c \cdot s, \tau = 0$)
Curva planar cuja curvatura varia linearmente com o comprimento de arco. Seus pontos de inflexão e rotação de curvatura são essenciais no projeto de curvas de transição rodoviária e ferroviária.
```bash
python3 teorema-fundamental-curvas.py "s" "0" -i -5 5 -o clothoid.html
```
*Arquivo padrão gerado:* `espiral_de_cornu-ks-t0-I-5_5.html`

### 6. Espiral Logarítmica ($\kappa(s) = \frac{1}{a s + b}, \tau = 0$)
Curva planar equipotencial cuja curvatura decresce inversamente ao comprimento de arco, mantendo constante o ângulo entre a reta tangente e o raio vetor polar.
```bash
python3 teorema-fundamental-curvas.py "1/(s + 1)" "0" -i 0 10 -o espiral_log.html
```
*Arquivo padrão gerado:* `espiral_logaritmica-k1_div_s_plus_1-t0-I0_10.html`

### 7. Curva Plana Geral ($\tau \equiv 0$)
Qualquer curva com torção identicamente nula mas curvatura arbitrária não constante (e.g., polinomial ou oscilatória). O movimento permanece confinado a um plano euclidiano 2D.
```bash
python3 teorema-fundamental-curvas.py "2 + sin(s)" "0" -i 0 10
```
*Arquivo padrão gerado:* `curva_plana-k2_plus_sin_s-t0-I0_10.html`

### 8. Curva Espacial Geral ($\tau \not\equiv 0$)
Curvas tridimensionais genuínas com curvatura e torção variáveis arbitrárias que não se enquadram nas classes anteriores.
```bash
python3 teorema-fundamental-curvas.py "1 + 0.5*cos(s)" "0.5*s" -i 0 10
```
*Arquivo padrão gerado:* `curva_espacial-k1_plus_0_5_mult_cos_s-t0_5_mult_s-I0_10.html`

---

## Interface Interativa Dual (2D e 3D) e Recursos Visuais

A visualização gerada é uma aplicação web autônoma e completa empacotada em um único arquivo HTML gerado pelo Plotly. O sistema chaveia deterministicamente entre renderização 2D e 3D de acordo com a geometria da curva:

```
┌────────────────────────────────────────────────────────────────────────┐
│  Teorema Fundamental de Curvas ── [ circulo | helice_circular ]        │
│                                                                        │
│   ┌─── HUD Card (Glassmorphic) ────────┐                               │
│   │ s: 3.1416                          │    (Modo 2D Cartesiano ou     │
│   │ r: (x, y) [2D] ou (x, y, z) [3D]   │     Modo 3D WebGL)            │
│   │ T: [Tx, Ty] (verde)                │       ● r(s)                  │
│   │ N: [Nx, Ny] (vermelho)             │      /|\  T(verde), N(vermelho)│
│   │ B: [Bx, By, Bz] (azul, em 3D)      │     / | \ B(azul, apenas 3D)  │
│   │ κ: 1.000000 | τ: 0.000000          │    [Reta Tangente / Normal]   │
│   │ ρ: 1.000000                        │    [Círculo Osculador]        │
│   └────────────────────────────────────┘                               │
│                                                                        │
│  [◄] [►] ───●───────────────────────────────────────────────────────   │
│          s = 3.1416 / 6.2832 (Clique na curva para navegar)            │
└────────────────────────────────────────────────────────────────────────┘
```

### Visualização Puramente 2D para Curvas Planas ($\tau \equiv 0$)
Quando a torção é identicamente nula, a curva é renderizada estritamente no espaço cartesiano 2D utilizando `go.Scatter` (sem inicialização de contexto 3D WebGL nem rotações de câmera esférica):
- **Escala Geométrica Rígida 1:1:** O layout é configurado com `yaxis=dict(scaleanchor="x", scaleratio=1)`, garantindo proporção euclidiana perfeita de 1 unidade em $y$ para 1 unidade em $x$. Isso impede rigorosamente que o círculo osculador deforme em elipse durante o zoom, pan ou redimensionamento de janela.
- **Aparato Planar Especializado (7 Traços com Legenda Interativa):**
  1. *Curva $r(s)$*: Trajetória no plano $xy$ colorida de acordo com a curvatura ou gradiente de $s$.
  2. *Ponto Ativo $r(s_i)$*: Marcador esférico de destaque na posição $(x_i, y_i)$.
  3. *Vetor Tangente $\vec{T}(s)$*: Seta verde unitária tangente à curva.
  4. *Vetor Normal Principal $\vec{N}(s)$*: Seta vermelha unitária perpendicular ao vetor velocidade.
  5. *Reta Tangente $L_T(u)$*: Linha tracejada tangente estendida no ponto ativo.
  6. *Reta Normal $L_N(u)$*: Linha tracejada ortogonal passando pelo centro de curvatura.
  7. *Círculo Osculador*: Circunferência no plano $xy$ centrada em $c(s) = r(s) + \rho(s) \vec{N}(s)$ com raio $\rho(s) = 1/|\kappa(s)|$.
- **HUD Bidimensional Glassmorphic:** Exibe $(x, y)$, componentes $[T_x, T_y]$, $[N_x, N_y]$, $\kappa(s)$, torção fixa `0.000 (Plana)` e raio de curvatura $\rho(s)$.

### Visualização 3D WebGL para Curvas Espaciais ($\tau \not\equiv 0$)
Para curvas com torção não nula, o motor instancia uma cena tridimensional interativa acelerada via WebGL:
- **Aparato Tridimensional Completo (10 Traços com Legenda Interativa):**
  1. *Curva $r(s)$*: Linha tridimensional contínua em $\mathbb{R}^3$.
  2. *Ponto Ativo $r(s_i)$*: Marcador esférico de destaque na posição tridimensional $(x_i, y_i, z_i)$.
  3. *Vetor Tangente $\vec{T}(s)$*: Segmento cônico destacado em **verde**.
  4. *Vetor Normal $\vec{N}(s)$*: Segmento cônico destacado em **vermelho**.
  5. *Vetor Binormal $\vec{B}(s)$*: Segmento cônico destacado em **azul**.
  6. *Reta Tangente*: Segmento linear estendido tangencialmente através do ponto ativo.
  7. *Plano Osculador*: Superfície poligonal semitransparente gerada no plano $\{\vec{T}, \vec{N}\}$.
  8. *Plano Normal*: Superfície semitransparente gerada no plano $\{\vec{N}, \vec{B}\}$.
  9. *Plano Retificante*: Superfície semitransparente gerada no plano $\{\vec{T}, \vec{B}\}$.
  10. *Círculo Osculador*: Círculo tridimensional com raio $\rho(s) = 1/\kappa(s)$ repousando no plano osculador.
- **HUD Tridimensional Glassmorphic:** Exibe $(x, y, z)$, componentes $\{T, N, B\}$, $\kappa(s)$, $\tau(s)$ e $\rho(s)$.

### Layout Responsivo 100vw $\times$ 100vh
- Reset completo de CSS (`margin: 0`, `padding: 0`, `overflow: hidden`).
- Dimensões fixadas via unidade moderna de viewport dinâmico `100dvh` e `100vw`, eliminando quaisquer barras de rolagem indesejadas em dispositivos móveis e desktops.
- Event listener JavaScript para `window.resize` com `Plotly.Plots.resize` automático.

### Controle Deslizante (Slider) e Animação Seletiva
- Slider inferior interativo que permite percorrer continuamente o parâmetro de comprimento de arco $s$ de $s_0$ a $s_1$.
- Otimização de renderização de alto desempenho: os frames de animação atualizam seletivamente apenas os traços dinâmicos do aparato, preservando a geometria da curva estática em cache na memória gráfica.

### Navegação Click-to-Point (`plotly_click`)
- Ao clicar em qualquer ponto da curva (seja em 2D ou 3D), um ouvinte de eventos `plotly_click` intercepta o evento, extrai o índice exato através do array `customdata` e sincroniza instantaneamente a posição do slider e todo o aparato diferencial para o ponto selecionado.

### Cartão Flutuante HUD (Heads-Up Display)
Um painel flutuante estilizado em *glassmorphism* (efeito de vidro com transparência e desfoque de fundo) exibe as grandezas métricas locais em tempo real com atualização ultra-rápida via JavaScript direto no DOM.

---

## Arquitetura de Software e Motor Matemático

O projeto segue rigorosos princípios de separação de responsabilidades e robustez numérica:

```
┌──────────────────────────────────────────────────────────┐
│              teorema-fundamental-curvas.py              │
│               CLI Entrypoint & Argparse                  │
└────────────────────────────┬─────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌───────────────────────────┐ ┌───────────────────────────┐
│      curva_engine.py      │ │       curva_viz.py        │
│  - Whitelist AST Segura   │ │  - 10-Trace 3D Scene      │
│  - SymPy / NumPy Lambdify │ │  - Full-screen HTML Shell │
│  - solve_ivp (DOP853/RK45)│ │  - Custom JS Injection    │
│  - Gram-Schmidt SO(3)     │ │  - Glassmorphic HUD Card  │
│  - 8-Class Classifier     │ │  - Slider & Animation     │
└───────────────────────────┘ └───────────────────────────┘
```

### Módulos do Sistema e Responsabilidades

- **`teorema-fundamental-curvas.py`**: Ponto de entrada CLI (*Command Line Interface*), suportando argumentos posicionais e flags opcionais (`-k`, `-t`, `-i`, `-n`, `-o`), validação rigorosa de limites de intervalo contra injeção de código, chaveamento automático de relatório entre reconstrução 2D e 3D, tratamento de exceções amigável ao usuário e códigos de saída semânticos (0, 1, 2).
- **`curva_engine.py`**: Motor analítico e numérico contendo:
  - *Análise Segura de Expressões (AST Whitelist)*: Bloqueio estrito de chamadas a `__import__`, `eval`, `exec` ou acesso a atributos privados, autorizando apenas operações aritméticas e funções transcendentais válidas.
  - *Pré-checagem de Singularidades*: Verificação analítica e numérica prévia de divisões por zero ou singularidades no domínio de integração.
  - *Reconstrução Planar por Quadratura (`reconstruct_plane_curve`)*: Quando $\tau(s) \equiv 0$, calcula diretamente o ângulo tangente $\theta(s) = \int \kappa(u)\,du$ e a trajetória $r(s) = \int (\cos\theta, \sin\theta)\,du$ via regra de Simpson cumulativa com interpolação `CubicSpline`, sem invocar integradores de EDOs.
  - *Integrador Numérico de EDOs 3D (`reconstruct_curve`)*: Para curvas espaciais ($\tau \not\equiv 0$), integração de alta ordem com `scipy.integrate.solve_ivp` (métodos DOP853 ou RK45, tolerâncias $rtol = 10^{-9}$ e $atol = 10^{-9}$).
  - *Preservação da Estrutura $SO(3)$*: Ortonormalização contínua de Gram-Schmidt Modificado restaurando a binormal por $B = T \times N$ e garantindo $\det(F(s)) = +1$ e $\|T\|=\|N\|=\|B\|=1$ a cada passo.
  - *Classificador Determinístico*: Identificação exata da geometria intrínseca em 8 classes.
  - *Geração de Nomenclatura Higienizada*: Formatação padronizada e segura de nomes de arquivo.
- **`curva_viz.py`**: Gerador da cena interativa em Plotly:
  - *Modo Dual Automático*: Dispatcher `build_curve_figure` que constrói cena cartesiana 2D para curvas planas ou cena WebGL 3D para curvas espaciais.
  - *Cena Planar 2D (7 Traços)*: Curva, Ponto Ativo, Vetores $\{T, N\}$, Retas Tangente e Normal, e Círculo Osculador com proporção rígida 1:1 (`scaleanchor="x", scaleratio=1`).
  - *Cena Espacial 3D (10 Traços)*: Curva, Ponto Ativo, Triedro unitário $\{T, N, B\}$, Reta Tangente, Planos Osculador, Normal e Retificante, e Círculo Osculador 3D.
  - *Animação e Slider Otimizados*: Frames seletivos de animação que atualizam apenas a geometria dinâmica sem sobrecarregar a memória da GPU.
  - *Shell HTML Responsivo*: Layout dinâmico sem barras de rolagem ocupando `100vw` $\times$ `100vh` (`100dvh`).
  - *Injeção de JavaScript Customizado*: Listener de redimensionamento de janela, sincronização do slider inferior e navegação click-to-point via evento `plotly_click` com dados mapeados por `customdata`.
  - *HUD Glassmorphic*: Cartão flutuante estilizado adaptável (exibindo grandezas 2D para curvas planas e 3D para espaciais) com atualização em tempo real.
- **`tests/`**: Suíte de testes abrangente com 244 testes automatizados cobrindo exaustivamente precisão numérica, quadratura planar, integradores de EDOs, segurança contra injeção e renderização.

---

## Bateria de Testes Automatizados (244 Testes)

O projeto conta com uma suíte exaustiva de testes automatizados com `pytest`, totalizando **244 testes rigorosos** aprovados com 100% de êxito.

### Estrutura dos Níveis de Teste

| Nível (Tier) | Arquivo de Teste | Qtd | Escopo Verificado |
|---|---|:---:|---|
| **Modelos Oráculo & Álgebra** | `test_teorema_fundamental.py` | 4 | Verificação de formas fechadas analíticas e ortonormalização $SO(3)$ exata. |
| **Tier 1 (Funcional)** | `test_teorema_fundamental.py` | 32 | Cobertura de integração ODE, frames ortonormais, classificação das 8 famílias, CLI e HTML. |
| **Tier 2 (Casos de Borda)** | `test_teorema_fundamental.py` | 16 | Casos limites: $\kappa = 0$, singularidades, domínios negativos, validação de AST contra injeção. |
| **Tier 3 (Combinações Cruzadas)** | `test_teorema_fundamental.py` | 5 | Curvatura/torção variáveis, Teorema de Lancret, espirais de Cornu e logarítmica. |
| **Tier 4 (Benchmarks Analíticos)** | `test_teorema_fundamental.py` | 7 | Precisão analítica $< 10^{-3}$ (semicírculo $R=0.5$, hélice circular, isometria $SE(3)$, clotoide). |
| **Curvas Planas 2D (Quadratura)** | `test_teorema_curvas_planas_2d.py` | 9 | Verificação de bypass total do `solve_ivp` para $\tau=0$, fechamento de círculo $< 10^{-14}$, diedro 2D, layout cartesiano 1:1 e traços 2D. |
| **Tier 5 & Hardening Adversarial** | `test_adversarial_tier5.py`, `test_adversarial_m4.py`, `test_curva_engine_stress.py`, `test_curva_viz_stress.py`, `test_adversarial_m2.py` | 171 | Testes adversariais de AST, resiliência do visualizador Plotly, estabilidade numérica de integradores e segurança. |
| **Total** | — | **244** | **100% dos testes aprovados.** |

### Como Executar os Testes

Para executar toda a suíte de testes com relatório verboso:
```bash
pytest -v
```

Para executar apenas a suíte de curvas planas e testes analíticos fundamentais:
```bash
pytest -v tests/test_teorema_curvas_planas_2d.py tests/test_teorema_fundamental.py
```

---

## Licença

Este projeto é disponibilizado sob a licença [MIT](LICENSE). Consulte o arquivo de licença para maiores detalhes.
