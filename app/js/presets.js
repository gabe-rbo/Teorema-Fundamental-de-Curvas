/* Gallery presets. params are the values of the sliders a, b, c used in the expressions. */
(function (root) {
  "use strict";
  var P = function (id, name, k, t, s0, s1, note, params) {
    return { id: id, name: name, k: k, t: t, s0: s0, s1: s1, note: note, params: params || [1, 1, 1] };
  };
  (root.Triedro = root.Triedro || {}).PRESETS = [
    // classics
    P("circulo", "Círculo", "1", "0", 0, 6.2832, "κ constante e τ nula: o círculo de raio 1/κ."),
    P("helice-circular", "Hélice circular", "1", "0.5", 0, 25, "κ e τ constantes: a hélice sobre um cilindro."),
    P("clotoide", "Clotoide", "s", "0", 0, 5, "κ(s) = s: espiral de Cornu, resolvida por integrais de Fresnel."),
    P("espiral-logaritmica", "Espiral logarítmica", "1/(s+1)", "0", 0, 12, "1/κ linear em s: ângulo constante com o raio vetor."),
    // planar
    P("rosacea", "Rosácea de cinco pétalas", "2+2*cos(5*s)", "0", 0, 12.5, "κ oscila entre 0 e 4: laços e pontos de inflexão."),
    P("cardioide", "Curvatura de cardioide", "1+cos(s)", "0", 0, 25.1, "κ toca zero a cada período: a curva respira entre laços."),
    P("espiral-exponencial", "Espiral exponencial", "exp(s/3)", "0", 0, 6, "A curvatura cresce exponencialmente: enrola cada vez mais apertado."),
    P("espiral-raiz", "Espiral de raiz", "sqrt(1+s)", "0", 0, 20, "κ = √(1+s): uma espiral entre a clotoide e o círculo."),
    P("clotoide-deslocada", "Clotoide deslocada", "0.5+s", "0", 0, 6, "κ = 0,5 + s: integrais de Fresnel com parâmetro de deslocamento."),
    P("pulso-gaussiano", "Pulso gaussiano", "3*exp(-(s-4)^2)+0.2", "0", 0, 8, "Quase reta, curva-se bruscamente em s = 4 e volta."),
    P("batimento-planar", "Batimento", "1+sin(s)*cos(3*s)", "0", 0, 20, "Dois harmônicos em batimento: caminho entrelaçado."),
    P("transicao-tanh", "Transição suave", "1+tanh(s-5)", "0", 0, 10, "Quase reta até s = 5, depois curvatura 2, em transição suave."),
    P("espiral-inversa", "Espiral inversa", "1/(1+s^2)", "0", 0, 30, "κ decai como 1/(1+s²): espiral que se abre devagar."),
    P("lacos-sen2", "Laços de sen²", "0.3+3*sin(s)^2", "0", 0, 18, "κ ≥ 0,3 com picos de 3,3: laços regulares."),
    P("sinuosa", "Curva sinuosa (κ com sinal)", "2*sin(s)", "0", 0, 12.5, "κ muda de sinal: a curva alterna entre virar à esquerda e à direita."),
    P("serpente", "Serpente", "3*cos(s)*exp(-s/10)", "0", 0, 30, "Ondulação que se amortece com o comprimento de arco."),
    // spatial
    P("helice-conica", "Hélice cônica", "2*exp(-s/6)", "2", 0, 20, "κ decai com τ constante: a hélice afina em cone."),
    P("torcao-linear", "Torção linear", "1", "s/2", 0, 14, "τ cresce linearmente: o plano osculador gira cada vez mais depressa."),
    P("torcao-oscilante", "Torção oscilante", "1.5", "3*sin(s)", 0, 20, "O sentido da hélice se inverte a cada meio período."),
    P("mola-modulada", "Mola modulada", "1+0.5*sin(s)", "0.5+cos(2*s)", 0, 25, "κ e τ oscilam em frequências 1 e 2: mola com pulsação."),
    P("transicao-destrogira", "Destrógira para levógira", "1.5", "3*tanh(s-8)", 0, 16, "τ muda de −3 a +3: uma hélice vira a hélice oposta."),
    P("batimento-espacial", "Batimento espacial", "2+sin(3*s)", "1+0.5*cos(5*s)", 0, 14, "Frequências incomensuráveis: a curva nunca se repete."),
    P("lancret", "Hélice de Lancret", "sqrt(1+s)", "2*sqrt(1+s)", 0, 14, "τ/κ = 2 constante: ângulo fixo com um eixo (teorema de Lancret)."),
    P("alta-frequencia", "Curvatura de alta frequência", "3+2*sin(5*s)", "1", 0, 12, "κ oscila 5 vezes mais rápido que o giro: franjas na hélice."),
    P("modulo-seno", "Módulo do seno", "abs(sin(s))+0.4", "2*abs(cos(s))", 0, 18, "κ e τ com cantos: segmentos de arco encadeados."),
    P("torcao-satura", "Torção que satura", "1+0.5*cos(s)", "2*tanh(s/3)", 0, 24, "τ → 2: a curva tende a uma hélice modulada."),
    P("torcao-composta", "Torção composta", "2", "sin(s)+sin(sqrt(2)*s)", 0, 30, "Seno somado a sen(√2·s): quase periódica."),
    P("curvatura-pulsante", "Curvatura pulsante", "1+sin(s)^2", "1+cos(s)^2", 0, 18, "Ambas oscilam com sen² e cos²: simetria de fase."),
    P("espiral-torcida", "Espiral torcida", "0.4+0.3*s", "1.5", 0, 12, "κ cresce linearmente com τ fixa: espiral que sobe enrolando."),
    P("rosa-espacial", "Rosa espacial", "2+2*cos(3*s)", "1+sin(2*s)", 0, 18, "A rosácea de três pétalas levantada pela torção."),
    // use the a, b, c sliders
    P("mola-parametrica", "Mola paramétrica (a, b, c)", "a+b*sin(c*s)", "1", 0, 30, "Arraste a, b e c no painel: κ = a + b·sen(c·s) com τ = 1.", [1.4, 0.8, 1.7]),
    P("rosa-parametrica", "Rosácea paramétrica (a, b, c)", "a+b*cos(c*s)", "0", 0, 18, "Mude c para mudar o número de pétalas em tempo real.", [2, 2, 5])
  ];
})(typeof self !== "undefined" ? self : this);
