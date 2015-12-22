from matplotlib.patches import Ellipse
import numpy as np

def covarianceEllipse(mean, covar, scale=1.0):
    eval, evec = np.linalg.eig(covar)
    angles = np.degrees(np.arctan2(evec[1,:], evec[0,:]))
    #print angles
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
    #plt.arrow(mean[0], mean[1], evec[0,0], evec[1,0])
    #plt.arrow(mean[0], mean[1], evec[0,1], evec[1,1])
    return e

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
