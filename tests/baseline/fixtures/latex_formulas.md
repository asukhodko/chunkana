# LaTeX Formulas Document

This document contains various LaTeX formulas for testing LaTeX block handling.

## Inline Math

The quadratic formula is $x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$ which solves $ax^2 + bx + c = 0$.

## Display Math

The Euler's identity is one of the most beautiful equations:

$$
e^{i\pi} + 1 = 0
$$

## Complex Equations

The Schrödinger equation describes quantum mechanics:

$$
i\hbar\frac{\partial}{\partial t}\Psi(\mathbf{r},t) = \hat{H}\Psi(\mathbf{r},t)
$$

## Matrix Notation

A rotation matrix in 2D:

$$
R(\theta) = \begin{pmatrix}
\cos\theta & -\sin\theta \\
\sin\theta & \cos\theta
\end{pmatrix}
$$

## Summation and Integration

The Riemann zeta function:

$$
\zeta(s) = \sum_{n=1}^{\infty} \frac{1}{n^s} = \prod_{p \text{ prime}} \frac{1}{1-p^{-s}}
$$

The Gaussian integral:

$$
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
$$

## Aligned Equations

Maxwell's equations in differential form:

$$
\begin{aligned}
\nabla \cdot \mathbf{E} &= \frac{\rho}{\varepsilon_0} \\
\nabla \cdot \mathbf{B} &= 0 \\
\nabla \times \mathbf{E} &= -\frac{\partial \mathbf{B}}{\partial t} \\
\nabla \times \mathbf{B} &= \mu_0\mathbf{J} + \mu_0\varepsilon_0\frac{\partial \mathbf{E}}{\partial t}
\end{aligned}
$$

## Conclusion

LaTeX blocks should be preserved as atomic units during chunking.
