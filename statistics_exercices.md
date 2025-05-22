
# Exercices d'Application de la Théorie des Probabilités

## Problème 1 : Analyse de Fiabilité des Réseaux

### Énoncés

1) Un réseau comprend cinq nœuds A,B,C,D,E qui fonctionnent indépendamment avec une probabilité $p=0.9$. Il existe trois chemins de A à E: A-B-E, A-C-E et A-D-E. Calculez la probabilité que A puisse communiquer avec E.

2) Considérons un système en série de $n$ nœuds, chacun fonctionnant indépendamment avec une probabilité $p$. Démontrez que lorsque $n \to \infty$, la fiabilité du système $R(n,p) \sim p^n$. Si l'on veut maintenir $R(n,p) \geq \alpha$, déterminez la relation entre $n$ et $p$.

3) Pour un composant avec un taux de défaillance exponentiel $\lambda(t)=\lambda_0 e^{\beta t}$, dérivez sa fonction de fiabilité $R(t)$ et son temps moyen jusqu'à défaillance MTTF.

### Solutions

#### 1) Analyse du système en parallèle
- Fiabilité d'un seul chemin: $p^2 = 0.9^2 = 0.81$
- Fiabilité du système: $R = 1-(1-0.81)^3 = 1-0.19^3 = 0.993141$

#### 2) Analyse du système en série
- Fiabilité: $R(n,p) = p^n$
- Pour maintenir $R(n,p) \geq \alpha$:
  $p^n \geq \alpha$
  $n \cdot \ln(p) \geq \ln(\alpha)$
  $n \leq \ln(\alpha)/\ln(p)$
- Valeur maximale: $n_{max} = \lfloor\ln(\alpha)/\ln(p)\rfloor$
- Comportement asymptotique: quand $p \to 1$, $\ln(p) \approx -(1-p)$, donc $n_{max} \approx -\ln(\alpha)/(1-p)$

#### 3) Analyse de fiabilité avec taux de défaillance exponentiel
- Fonction de fiabilité:
  $R(t) = \exp\left(-\int_0^t \lambda(u)du\right)$
  $= \exp\left(-\int_0^t \lambda_0 e^{\beta u}du\right)$
  $= \exp\left(-\frac{\lambda_0}{\beta}(e^{\beta t}-1)\right)$

- Temps moyen jusqu'à défaillance:
  $MTTF = \int_0^\infty R(t)dt = \int_0^\infty \exp\left(-\frac{\lambda_0}{\beta}(e^{\beta t}-1)\right)dt$
  
  Par substitution $v = e^{\beta t}$:
  $t = \frac{1}{\beta}\ln(v)$, $dt = \frac{1}{\beta}\frac{1}{v}dv$
  
  $MTTF = \int_1^\infty \exp\left(-\frac{\lambda_0}{\beta}(v-1)\right)\frac{1}{\beta}\frac{1}{v}dv$
  $= \frac{1}{\beta}e^{\frac{\lambda_0}{\beta}}\int_1^\infty v^{-1}e^{-\frac{\lambda_0}{\beta}v}dv$
  $= \frac{1}{\beta}e^{\frac{\lambda_0}{\beta}}E_1\left(\frac{\lambda_0}{\beta}\right)$

  où $E_1$ est la fonction intégrale exponentielle.

## Problème 2 : Analyse des Circuits Aléatoires

### Énoncés

1) Dans un circuit, une résistance $R$ suit une distribution normale $N(R_0,\sigma^2)$. Trouvez la moyenne et la variance de la puissance $P=V^2/R$, où $V$ est une tension constante.

2) Un filtre a une fonction de transfert $H(z)=1/(1-az^{-1})$, où $|a|<1$ est un paramètre aléatoire suivant une distribution uniforme $U[0,0.5]$. Calculez le gain d'énergie du filtre $E[|H(e^{j\omega})|^2]$ aux points $\omega=0$ et $\omega=\pi$.

3) Dans un circuit intégré, deux condensateurs $C_1$ et $C_2$ suivent indépendamment une distribution normale $N(\mu,\sigma^2)$. Définissons la constante de temps $\tau=C_1C_2/(C_1+C_2)$, trouvez la fonction de densité de probabilité de $\tau$.

### Solutions

#### 1) Analyse statistique de la puissance
- Pour $R \sim N(R_0,\sigma^2)$ et $P=V^2/R$:

  Par développement de Taylor:
  $E[P] \approx \frac{V^2}{R_0} + \frac{V^2\sigma^2}{R_0^3}$
  $Var[P] \approx \frac{V^4\sigma^2}{R_0^4} + \frac{3V^4\sigma^4}{R_0^6}$

  Pour $\sigma/R_0$ petit:
  $E[P] \approx \frac{V^2}{R_0}\left(1 + \frac{\sigma^2}{R_0^2}\right)$
  $Var[P] \approx \frac{V^4\sigma^2}{R_0^4}\left(1 + \frac{3\sigma^2}{R_0^2}\right)$

#### 2) Gain d'énergie du filtre aléatoire
- Gain d'énergie: $|H(e^{j\omega})|^2 = \frac{1}{|1-ae^{-j\omega}|^2} = \frac{1}{1-2a\cdot\cos(\omega)+a^2}$
  
  Pour $\omega=0$: $|H(e^{j0})|^2 = \frac{1}{(1-a)^2}$
  
  Pour $\omega=\pi$: $|H(e^{j\pi})|^2 = \frac{1}{(1+a)^2}$
  
  Avec $a \sim U[0,0.5]$ et $f(a) = 2, 0 \leq a \leq 0.5$:
  
  $E[|H(e^{j0})|^2] = \int_0^{0.5} \frac{1}{(1-a)^2} \cdot 2 da = 2\left[-\frac{1}{1-a}\right]_0^{0.5} = 2\left[\frac{1}{1-0.5} - \frac{1}{1-0}\right] = 2[2-1] = 2$
  
  $E[|H(e^{j\pi})|^2] = 2\int_0^{0.5} \frac{1}{(1+a)^2} da = 2\left[-\frac{1}{1+a}\right]_0^{0.5} = 2\left[\frac{1}{1+0} - \frac{1}{1+0.5}\right] = 2\left[1-\frac{2}{3}\right] = \frac{2}{3}$

#### 3) Distribution de la constante de temps
- Pour $\tau=\frac{C_1C_2}{C_1+C_2}$ avec $C_1,C_2 \sim N(\mu,\sigma^2)$:
  
  Pour $\sigma/\mu$ petit:
  $E[\tau] \approx \frac{\mu}{2}$
  $Var[\tau] \approx \frac{\sigma^2}{8}$
  
  Pour $\mu \gg \sigma$: $\tau \sim N\left(\frac{\mu}{2}, \frac{\sigma^2}{8}\right)$ approximativement

## Problème 3 : Traitement des Signaux Aléatoires

### Énoncés

1) Un signal $x(t)$ passe par un système linéaire invariant dans le temps $h(t)$, produisant une sortie $y(t)=x(t)*h(t)$. Si $x(t)$ est un processus aléatoire WSS avec une moyenne $\mu_x$ et une fonction d'autocorrélation $R_x(\tau)$, trouvez la moyenne $\mu_y$ et la fonction d'autocorrélation $R_y(\tau)$ de $y(t)$.

2) Le processus aléatoire $Z(t) = X(t)Y(t)$ est le produit de deux processus gaussiens WSS indépendants $X(t)$ et $Y(t)$, avec des moyennes $\mu_x$ et $\mu_y$, et des variances $\sigma_x^2$ et $\sigma_y^2$ respectivement. Trouvez la moyenne, la variance et la fonction d'autocorrélation de $Z(t)$.

3) Un signal aléatoire $x[n]$ passe par un filtre autorégressif $y[n]=0.8y[n-1]+x[n]$, où $x[n]$ est un bruit blanc de moyenne nulle et de variance 1. Calculez la moyenne, la variance et la fonction d'autocorrélation de $y[n]$.

### Solutions

#### 1) Système linéaire invariant dans le temps
- Moyenne de sortie:
  $\mu_y = E[y(t)] = E\left[\int_{-\infty}^{\infty} x(t-\tau)h(\tau)d\tau\right] = \mu_x\int_{-\infty}^{\infty} h(\tau)d\tau = \mu_x H(0)$

- Fonction d'autocorrélation:
  $R_y(\tau) = R_x(\tau) * h(\tau) * h(-\tau)$
  
  Dans le domaine fréquentiel:
  $S_y(\omega) = S_x(\omega)|H(\omega)|^2$

#### 2) Produit de processus aléatoires
- Moyenne: $\mu_Z = E[Z(t)] = E[X(t)Y(t)] = \mu_x\mu_y$

- Variance:
  $Var[Z(t)] = E[(X(t)Y(t)-\mu_x\mu_y)^2]$
  $= E[X^2(t)Y^2(t)]-2\mu_x\mu_yE[X(t)Y(t)]+\mu_x^2\mu_y^2$
  $= E[X^2(t)]E[Y^2(t)]-2\mu_x\mu_y \cdot \mu_x\mu_y+\mu_x^2\mu_y^2$
  $= (\sigma_x^2+\mu_x^2)(\sigma_y^2+\mu_y^2)-\mu_x^2\mu_y^2$
  $= \sigma_x^2\sigma_y^2+\mu_x^2\sigma_y^2+\mu_y^2\sigma_x^2$

- Fonction d'autocorrélation:
  $R_Z(\tau) = E[Z(t)Z(t+\tau)] = E[X(t)Y(t)X(t+\tau)Y(t+\tau)]$
  $= E[X(t)X(t+\tau)]E[Y(t)Y(t+\tau)] = R_x(\tau)R_y(\tau)$

#### 3) Filtre autorégressif
- Moyenne:
  $\mu_y = 0.8\mu_y + 0 \Rightarrow \mu_y = 0$

- Variance:
  $Var[y[n]] = E[(0.8y[n-1]+x[n])^2]$
  $= 0.64E[y^2[n-1]]+0+E[x^2[n]]$
  $= 0.64Var[y[n]]+1$
  $\Rightarrow Var[y[n]] = \frac{1}{1-0.64} = \frac{1}{0.36} = 2.778$

- Fonction d'autocorrélation:
  $R_y[k] = 0.8R_y[k-1]$ pour $k > 0$
  $R_y[0] = Var[y[n]] = 2.778$
  
  Par récurrence:
  $R_y[k] = 2.778 \times 0.8^{|k|}$