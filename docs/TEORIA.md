# Fundamentação Teórica: Teorema Fundamental de Curvas

Este documento apresenta o embasamento matemático rigoroso utilizado pelo motor computacional deste projeto, cobrindo o Teorema Fundamental das Curvas no $\mathbb{R}^3$ e no $\mathbb{R}^2$, o sistema de Frenet-Serret, a formulação matricial em Álgebra de Lie $\mathfrak{so}(3)$, o vetor de Darboux e os elementos do aparato diferencial local.

---

## 1. Teorema Fundamental das Curvas Espaciais ($\mathbb{R}^3$)

> **Teorema Fundamental da Teoria Local de Curvas no $\mathbb{R}^3$ (Existência e Unicidade):**
> Sejam $\kappa, \tau: [s_0, s_1] \to \mathbb{R}$ funções de classe $C^1$ (ou contínuas), tais que $\kappa(s) > 0$ para todo $s \in [s_0, s_1]$ (cf. **do Carmo**, 1976/2016, Seção 1-5; **Tenenblat**, 2008, Cap. 2; **Toponogov**, 2006, Seção 1.3; **Alencar, Santos & Frensel**, 2011, Cap. 2).
> 
> 1. **Existência:** Existe uma curva parametrizada pelo comprimento de arco $r: [s_0, s_1] \to \mathbb{R}^3$ de classe $C^3$ cuja curvatura é $\kappa(s)$ e cuja torção é $\tau(s)$.
> 2. **Unicidade a Menos de Movimento Rígido:** Se $\tilde{r}: [s_0, s_1] \to \mathbb{R}^3$ for outra curva com as mesmas funções de curvatura e torção, então existe uma isometria euclidiana direta própria $M \in \mathrm{SE}(3)$ (composta por uma rotação $R \in \mathrm{SO}(3)$ e uma translação $v \in \mathbb{R}^3$) tal que:
>    $$\tilde{r}(s) = R \, r(s) + v, \quad \forall s \in [s_0, s_1].$$

Pelo Teorema de Picard-Lindelöf (Cauchy-Lipschitz), dado um referencial inicial ortonormal orientado positivamente $\{T(s_0), N(s_0), B(s_0)\} \in \mathrm{SO}(3)$ e um ponto inicial $r(s_0) = r_0 \in \mathbb{R}^3$, o problema de valor inicial linear possui solução única global em todo o intervalo $[s_0, s_1]$. No referencial canônico padrão adotado:

$$r(s_0) = (0, 0, 0)^T, \quad T(s_0) = (1, 0, 0)^T, \quad N(s_0) = (0, 1, 0)^T, \quad B(s_0) = (0, 0, 1)^T$$

---

## 2. Teorema Fundamental das Curvas Planas ($\mathbb{R}^2$, Quadratura Direta)

Para curvas no plano euclidiano $\mathbb{R}^2$, a torção é identicamente nula ($\tau(s) \equiv 0$), o que implica que a binormal é constante ($B(s) \equiv (0, 0, 1)^T$) e o movimento fica estritamente restrito ao plano gerado pelo diedro de Frenet $\{T(s), N(s)\}$.

> **Teorema Fundamental da Teoria Local de Curvas Planas:**
> Seja $\kappa: [s_0, s_1] \to \mathbb{R}$ uma função contínua arbitrária (curvatura com sinal no plano, podendo ser positiva, nula ou negativa).
> 
> 1. **Existência:** Existe uma curva plana parametrizada pelo comprimento de arco $r: [s_0, s_1] \to \mathbb{R}^2$ de classe $C^2$ cuja curvatura com sinal é $\kappa(s)$.
>    Com a condição canônica inicial $r(s_0) = (0, 0)^T$ e $T(s_0) = (1, 0)^T$ ($\theta_0 = 0$), o ângulo da reta tangente $\theta(s)$ é obtido por **quadratura direta**:
>    $$\theta(s) = \theta_0 + \int_{s_0}^s \kappa(u)\,du$$
>    O referencial móvel planar (diedro ortonormal) é expresso imediatamente por:
>    $$T(s) = \begin{pmatrix} \cos \theta(s) \\ \sin \theta(s) \end{pmatrix}, \quad N(s) = \begin{pmatrix} -\sin \theta(s) \\ \cos \theta(s) \end{pmatrix}$$
>    E a trajetória da curva $r(s) = (x(s), y(s))$ resulta de uma segunda quadratura direta:
>    $$x(s) = \int_{s_0}^s \cos \theta(u)\,du, \quad y(s) = \int_{s_0}^s \sin \theta(u)\,du$$
> 2. **Unicidade a Menos de Movimento Rígido:** Se $\tilde{r}$ for outra curva plana com a mesma curvatura com sinal $\kappa(s)$, existe um movimento rígido próprio em $\mathrm{SE}(2)$ (rotação plana e translação) tal que $\tilde{r}(s) = R_\phi r(s) + v_0$.

**Otimização Numérica:**
Ao detectar $\tau \equiv 0$, o sistema dispensa o integrador de EDOs 3D (`scipy.integrate.solve_ivp`), aplicando integração por quadratura cumulativa de Simpson (`scipy.integrate.cumulative_simpson`) com interpolação cúbica (`CubicSpline`). O cálculo é completado em $< 1$ ms com erro de ortonormalidade em precisão de máquina ($|\|T\| - 1| < 10^{-15}$).

---

## 3. Sistema Diferencial de Frenet-Serret

O triedro móvel de Frenet é constituído pelos vetores unitários ortogonais:
- **Vetor Tangente Unitário:** $T(s) = \frac{dr}{ds}(s)$
- **Vetor Normal Principal:** $N(s) = \frac{1}{\kappa(s)} \frac{dT}{ds}(s)$
- **Vetor Binormal:** $B(s) = T(s) \times N(s)$

As taxas de variação desses vetores com respeito ao comprimento de arco $s$ satisfazem as **Equações de Frenet-Serret**:

$$\begin{aligned}
\frac{dr}{ds} &= T(s) \\
\frac{dT}{ds} &= \kappa(s) N(s) \\
\frac{dN}{ds} &= -\kappa(s) T(s) + \tau(s) B(s) \\
\frac{dB}{ds} &= -\tau(s) N(s)
\end{aligned}$$

Este sistema de 12 equações diferenciais ordinárias de primeira ordem (3 para posição e 9 para os vetores da base móvel) governa a evolução tridimensional da curva.

### Quando existe solução elementar?

O teorema garante que $\kappa(s)$ e $\tau(s)$ **determinam** a curva, mas não que ela possa ser escrita com funções elementares. O que se pode (ou não) resolver em forma fechada depende do caso:

| Caso | $r(s)$, $T$, $N$, $B$ | O que o programa exibe |
|---|---|---|
| $\kappa = 0$ | reta | forma fechada |
| $\kappa$ constante, $\tau = 0$ | círculo | forma fechada |
| $\kappa$, $\tau$ constantes | hélice circular | forma fechada (a menos de movimento rígido) |
| $\tau = 0$, $\kappa = cs + d$ | clotoide | integrais de Fresnel $C$, $S$ |
| $\tau = 0$, $1/\kappa = as + b$ | espiral logarítmica | forma fechada |
| $\tau = 0$, $\kappa$ qualquer | $T = (\cos\theta, \sin\theta)$ com $\theta = \int\kappa$ | $\theta$ resolvida quando a primitiva é elementar; $T$ e $N$ explícitos; $r(s)$ como integral com o integrando já explícito |
| $\tau \neq 0$, geral | **sem solução elementar** | $\int\kappa$ e $\int\tau$ resolvidas quando possível; $T' = \kappa N$ etc. com $\kappa$, $\tau$ substituídas; $r(s) = r(s_0) + \int T$ |

**Por que as curvas espaciais gerais não têm fórmula.** O sistema de Frenet-Serret $F' = \Omega(s) F$, com $\Omega$ antissimétrica de entradas $\kappa$ e $\tau$, é uma EDO linear com coeficientes variáveis. Para $\Omega$ arbitrária ela não tem solução em funções elementares, nem mesmo em quadraturas: as matrizes $\Omega(s_1)$ e $\Omega(s_2)$ não comutam em geral, então a exponencial $\exp\int\Omega$ não resolve o sistema. Escrever $T$, $N$, $B$ a partir de $\kappa$ e $\tau$ equivale a resolver a equação de Riccati associada (via projeção estereográfica de $SO(3)$ em $\mathbb{C}$), que é conhecida por não ter solução geral em quadraturas. Séries de Magnus ou de Picard convergem, mas não são formas fechadas. Por isso a curva é integrada numericamente (Magnus de 4ª ordem no aplicativo), e a única parte simbólica exata é a primitiva de $\kappa$ e de $\tau$.

**Por que mesmo no caso plano $r(s)$ pode ficar como integral.** Com $\theta$ explícito, $r(s) = \int (\cos\theta, \sin\theta)\,du$. Para $\theta$ linear, quadrática ou logarítmica há forma fechada (círculo, clotoide, espiral logarítmica). Para outros $\theta$, como $\theta = 2s - \tfrac13\cos 3s$, a primitiva só existe como série de Bessel (expansão de Jacobi-Anger), não como função elementar.

**Onde isso está no código.** A busca da primitiva falha, e cai na integral não resolvida, em `web/js/formulas.js` (função `antiderivative`, cada `ok = false` está comentado com o tipo de integrando que não cobre) e em `src/curva_viz.py` (`_solved_integral`, que lista as três situações de falha; e `_explicit_curve_formulas`, nos ramos plano e espacial genérico). Falhar ali não é erro: é uma propriedade do integrando.

---

## 4. Formulação Matricial e Álgebra de Lie $\mathfrak{so}(3)$

Denotando a matriz do referencial de Frenet como a matriz ortogonal $F(s) = [T(s) \mid N(s) \mid B(s)] \in \mathrm{SO}(3)$, a relação diferencial escreve-se:

$$\frac{dF}{ds}(s) = F(s) \, \Omega(s)$$

onde $\Omega(s)$ é um elemento da álgebra de Lie $\mathfrak{so}(3)$ (matrizes antissimétricas $3 \times 3$, $\Omega^T = -\Omega$):

$$\Omega(s) = \begin{pmatrix} 0 & -\kappa(s) & 0 \\ \kappa(s) & 0 & -\tau(s) \\ 0 & \tau(s) & 0 \end{pmatrix} \in \mathfrak{so}(3)$$

A antissimetria de $\Omega(s)$ garante analiticamente a conservação da ortonormalidade:

$$\frac{d}{ds} \left( F(s)^T F(s) \right) = \Omega(s)^T F^T F + F^T F \Omega(s) = -\Omega(s) + \Omega(s) = 0$$

Em integrações numéricas finitas, acumulações de erro de ponto flutuante podem degradar a ortonormalidade. O motor emprega um estágio de **Ortonormalização Modificada de Gram-Schmidt** com restauração exata da binormal por $B = T \times N$, garantindo $\det(F(s)) = +1$ e $\|T\| = \|N\| = \|B\| = 1$ com erro residual inferior a $10^{-9}$.

---

## 5. Vetor de Darboux e Rotação Instantânea

A rotação instantânea do triedro de Frenet à medida que o referencial percorre a curva com velocidade unitária é descrita pelo **Vetor de Darboux** $\omega(s) \in \mathbb{R}^3$:

$$\omega(s) = \tau(s) T(s) + \kappa(s) B(s)$$

As equações de Frenet-Serret são expressas de forma unificada pelo produto vetorial:

$$\frac{dT}{ds} = \omega(s) \times T(s), \quad \frac{dN}{ds} = \omega(s) \times N(s), \quad \frac{dB}{ds} = \omega(s) \times B(s)$$

A norma do vetor de Darboux $\|\omega(s)\| = \sqrt{\kappa(s)^2 + \tau(s)^2}$ representa a velocidade angular total do referencial com respeito a $s$. O eixo instantâneo de rotação tem a direção de $\omega(s)$, e a razão $\tau(s)/\kappa(s)$ governa a inclinação desse eixo em relação ao plano osculador.

---

## 6. Aparato Diferencial Local

Para cada ponto $r(s)$ com $\kappa(s) > 0$, definem-se os seguintes elementos geométricos locais:

### Plano Osculador
- **Vetor Normal:** $B(s)$ (direção binormal)
- **Equação:**
  $$(X - r(s)) \cdot B(s) = 0$$
- **Significado Geométrico:** Plano que melhor aproxima a curva na vizinhança de $r(s)$ (ordem de contato $\ge 2$). É gerado pela base $\{T(s), N(s)\}$.

### Plano Normal
- **Vetor Normal:** $T(s)$ (direção tangente)
- **Equação:**
  $$(X - r(s)) \cdot T(s) = 0$$
- **Significado Geométrico:** Plano ortogonal à direção de movimento $T(s)$. É gerado pela base $\{N(s), B(s)\}$.

### Plano Retificante
- **Vetor Normal:** $N(s)$ (direção normal principal)
- **Equação:**
  $$(X - r(s)) \cdot N(s) = 0$$
- **Significado Geométrico:** Plano ortogonal à aceleração normal. Contém a reta tangente $T(s)$ e a binormal $B(s)$, gerado por $\{T(s), B(s)\}$.

### Reta Tangente
- **Equação Paramétrica:**
  $$L_T(u) = r(s) + u \, T(s), \quad u \in \mathbb{R}$$
- **Significado Geométrico:** Direção infinitesimal da velocidade e deslocamento tangencial da curva.

### Círculo Osculador
- **Plano:** Contido no plano osculador (normal $B(s)$).
- **Centro e Raio:**
  $$c(s) = r(s) + \rho(s) N(s), \quad \rho(s) = \frac{1}{\kappa(s)}$$
- **Significado Geométrico:** Círculo com contato de **segunda ordem** com a curva em $r(s)$ (mesma posição $r(s)$, mesma reta tangente $T(s)$ e mesma curvatura $\kappa(s)$).

---

## 7. Referências Bibliográficas

1. **Toponogov, V. A.** (2006). *Differential Geometry of Curves and Surfaces: A Concise Guide*. Birkhäuser, Boston. ISBN: 978-0-8176-4384-3.
2. **Tenenblat, K.** (2008). *Introdução à Geometria Diferencial*. Edgard Blücher / Editora UnB, 2ª edição. ISBN: 978-85-212-0457-2.
3. **Alencar, H., Santos, W., Frensel, K.** (2011). *Geometria Diferencial das Curvas*. IMPA (Instituto de Matemática Pura e Aplicada), Rio de Janeiro. ISBN: 978-85-244-0331-6.
4. **do Carmo, M. P.** (1976). *Differential Geometry of Curves and Surfaces*. Prentice-Hall (reedição revisada Dover Publications, 2016). ISBN: 978-0-486-80699-0.
5. **Lancret, M. A.** (1806). *Mémoire sur les courbes à double courbure*. Mémoires présentés à l'Institut d'Égypte / Mémoires des savants étrangers, t. I, Paris, pp. 416–454 (apresentado em 1802).
