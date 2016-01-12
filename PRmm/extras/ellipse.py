from matplotlib.patches import Ellipse
import numpy as np

def covarianceEllipse(mean, covar, scale=1.0):
    eval, evec = np.linalg.eig(covar)
    angles = np.degrees(np.arctan(evec[1,:] / evec[0,:]))
    q1 = np.flatnonzero((angles >= 0) & (angles < 90))[0]
    q2 = 1 - q1
    q1Angle = angles[q1]
    q1Length = np.sqrt(eval[q1])
    q2Length = np.sqrt(eval[q2])
    e = Ellipse(xy=mean, angle=q1Angle,
                width=q1Length*scale, height=q2Length*scale)
    e.set_fill(False)
    e.set_edgecolor("black")
    e.set_alpha(1.0)
    e.set_lw(2)
    e.set_ls("dashed")
    return e

def covarianceEllipse3(mean, covar3, scale=1.0):
    # Take cov as [s_x, s_y, s_xy]
    covar = np.zeros(shape=(2,2))
    covar[0,0] = covar3[0]
    covar[1,1] = covar3[1]
    covar[0,1] = covar3[2]
    covar[1,0] = covar3[2]
    return covarianceEllipse(mean, covar, scale)

def covarianceEllipses3(means, covar3s, scale=1.0):
    return [ covarianceEllipse3(mean, covar3, scale)
             for (mean, covar3) in zip(means, covar3s) ]

def demo():
    from matplotlib import pyplot as plt
    mu = [1,1]
    cov = [[2, 0.5], [0.5, 1]]
    #cov = [[2, 0], [0, 1]]
    N = 10000
    X = np.random.multivariate_normal(mu, cov, N)
    plt.plot(X[:,0], X[:,1], '.', alpha=0.1)
    plt.axis("equal")
    ax = plt.gca()
    ax.add_artist(covarianceEllipse(mu, cov, 4))
    plt.show()

if __name__ == "__main__":
    demo()
