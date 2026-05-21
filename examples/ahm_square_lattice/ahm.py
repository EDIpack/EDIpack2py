import numpy as np
from edipack2py import global_env as ed
import mpi4py
from mpi4py import MPI
import os, sys

# INIT MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
print("I am process", rank, "of", comm.Get_size())
master = rank == 0


# Auxiliary functions
def superconductive_zeta(warray, xmu, Sigma_all, axis):
    Ntot = np.shape(Sigma_all)[2]
    Lfreq = np.shape(warray)[0]
    zi = np.zeros(
        (2, 2, Ntot, Ntot, Lfreq), dtype=complex
    )

    if axis == "m":
        zi[0, 0, :, :, :] = (warray + xmu) * np.eye(Ntot)[..., None] - Sigma_all[0]
        zi[0, 1, :, :, :] = -Sigma_all[1]
        zi[1, 0, :, :, :] = -Sigma_all[1]
        zi[1, 1, :, :, :] = (warray - xmu) * np.eye(Ntot)[..., None] + np.conj(
            Sigma_all[0]
        )
    elif axis == "r":
        warray_bar = warray[::-1, ...]
        Sigma_bar = Sigma_all[0, ..., ::-1]
        zi[0, 0, :, :, :] = (warray + xmu) * np.eye(Ntot)[..., None] - Sigma_all[0]
        zi[0, 1, :, :, :] = -Sigma_all[1]
        zi[1, 0, :, :, :] = -Sigma_all[1]
        zi[1, 1, :, :, :] = -np.conj(warray_bar + xmu) * np.eye(Ntot)[
            ..., None
        ] + np.conj(Sigma_bar)
    return zi


def get_gloc(warray, xmu, Hk, Sigma_all, axis):
    """
    Z has dimension  [Nambu,Nambu,Nso,Nso,Nfreq]
    Hk has dimension [Nnambu,Nk,Nso,Nso]
    Gk has dimension [Nk,Nnambu,Nso,Nso]
    Gmatrix has dimension [Nnambu*Ntot,Nnambu*Ntot,Nfreq]
    Returns an object of dimension [2,Ntot,Nfreq]
    """

    try:
        import mpi4py
        from mpi4py import MPI

        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()
        mpiflag = True
    except:
        mpiflag = False
        rank = 0
        size = 1

    master = rank == 0

    if master:
        print("Calculating local G axis " + axis + ":")

    Z = superconductive_zeta(warray, xmu, Sigma_all, axis)
    Ntot = np.shape(Sigma_all)[2]
    Nfreq = np.shape(Z)[-1]
    Nk = np.shape(Hk)[1]

    if Nk >= Nfreq:
        base = int(Nk // size)
        leftover = int(Nk % size)
        chunks = np.ones(size, dtype=int) * base
        chunks[:leftover] += 1
        offsets = np.zeros(size, dtype=int)
        offsets[1:] = np.cumsum(chunks)[:-1]
        ilow = offsets[rank]
        ihigh = ilow + chunks[rank]
        # print(rank,ilow,ihigh,chunks[rank])

        Gtmp = np.zeros((chunks[rank], 2 * Ntot, 2 * Ntot, Nfreq), dtype=complex)

        Gtmp[:, 0:Ntot, 0:Ntot, :] = Z[0, 0, :, :, :] - Hk[0, ilow:ihigh, :, :, None]
        Gtmp[:, 0:Ntot, Ntot : 2 * Ntot, :] = Z[0, 1, :, :, :]
        Gtmp[:, Ntot : 2 * Ntot, 0:Ntot, :] = Z[1, 0, :, :, :]
        Gtmp[:, Ntot : 2 * Ntot, Ntot : 2 * Ntot, :] = (
            Z[1, 1, :, :, :] - Hk[1, ilow:ihigh, :, :, None]
        )

        Gtmp = Gtmp.transpose(0, 3, 1, 2)
        Gtmp = np.linalg.inv(Gtmp)
        Gtmp = Gtmp.transpose(0, 2, 3, 1)
        if mpiflag:
            Gtmp = np.ascontiguousarray(np.sum(Gtmp, axis=0) / Nk)
            Gloc = np.zeros_like(Gtmp)
            comm.Allreduce(Gtmp, Gloc, op=MPI.SUM)
        else:
            Gloc = np.sum(Gtmp, axis=0) / Nk
    else:
        base = int(Nfreq // size)
        leftover = int(Nfreq % size)
        chunks = np.ones(size, dtype=int) * base
        chunks[:leftover] += 1
        offsets = np.zeros(size, dtype=int)
        offsets[1:] = np.cumsum(chunks)[:-1]
        ilow = offsets[rank]
        ihigh = ilow + chunks[rank]
        # print(rank,ilow,ihigh,chunks[rank])

        Gtmp = np.zeros((Nk, 2 * Ntot, 2 * Ntot, Nfreq), dtype=complex)
        Gloc = np.zeros((2 * Ntot, 2 * Ntot, Nfreq), dtype=complex)

        Gtmp[:, 0:Ntot, 0:Ntot, ilow:ihigh] = (
            Z[0, 0, :, :, ilow:ihigh] - Hk[0, :, :, :, None]
        )
        Gtmp[:, 0:Ntot, Ntot : 2 * Ntot, ilow:ihigh] = Z[0, 1, :, :, ilow:ihigh]
        Gtmp[:, Ntot : 2 * Ntot, 0:Ntot, ilow:ihigh] = Z[1, 0, :, :, ilow:ihigh]
        Gtmp[:, Ntot : 2 * Ntot, Ntot : 2 * Ntot, ilow:ihigh] = (
            Z[1, 1, :, :, ilow:ihigh] - Hk[1, :, :, :, None]
        )

        Gtmp = Gtmp.transpose(0, 3, 1, 2)
        Gtmp[:, ilow:ihigh, :, :] = np.linalg.inv(Gtmp[:, ilow:ihigh, :, :])
        Gtmp = Gtmp.transpose(0, 2, 3, 1)

        if mpiflag:
            Gtmp = np.ascontiguousarray(np.sum(Gtmp, axis=0) / Nk)
            comm.Allreduce(Gtmp, Gloc, op=MPI.SUM)
        else:
            Gloc = np.sum(Gtmp, axis=0) / Nk

    return np.stack((Gloc[:Ntot, :Ntot, :], Gloc[:Ntot, Ntot:, :]), axis=0)


def get_weiss_field(G, Sigma):
    """
    complex(8),dimension(2,Ntot,Ntot,Nfreq)              :: G
    complex(8),dimension(2,Ntot,Ntot,Nfreq)              :: Sigma
    """
    try:
        import mpi4py
        from mpi4py import MPI

        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()
        mpiflag = True
    except:
        mpiflag = False
        rank = 0
        size = 1

    master = rank == 0

    if master:
        print("Calculating Weiss Field")

    Ntot = np.shape(G)[1]
    Nfreq = np.shape(G)[-1]

    Gnambu = np.zeros((2 * Ntot, 2 * Ntot, Nfreq), dtype=complex)
    Snambu = np.zeros((2 * Ntot, 2 * Ntot, Nfreq), dtype=complex)

    Snambu[:Ntot, :Ntot, :] = Sigma[0, :, :, :]
    Snambu[:Ntot, Ntot:, :] = Sigma[1, :, :, :]
    Snambu[Ntot:, :Ntot, :] = Sigma[1, :, :, :]
    Snambu[Ntot:, Ntot:, :] = -np.conj(Sigma[0, :, :, :])

    Gnambu[:Ntot, :Ntot, :] = G[0, :, :, :]
    Gnambu[:Ntot, Ntot:, :] = G[1, :, :, :]
    Gnambu[Ntot:, :Ntot, :] = G[1, :, :, :]
    Gnambu[Ntot:, Ntot:, :] = -np.conj(G[0, :, :, :])

    Weiss = np.linalg.inv(
        np.linalg.inv(Gnambu.transpose(2, 0, 1)) + Snambu.transpose(2, 0, 1)
    ).transpose(1, 2, 0)

    return np.stack((Weiss[:Ntot, :Ntot, :], Weiss[:Ntot, Ntot:, :]), axis=0)


def generate_kgrid(Nk):
    b1 = 2 * np.pi * np.array([1.0, 0.0])
    b2 = 2 * np.pi * np.array([0.0, 1.0])
    n1, n2 = np.meshgrid(np.arange(Nk), np.arange(Nk))
    n1 = n1 / Nk
    n2 = n2 / Nk
    gridout = np.stack([n1.ravel(), n2.ravel()], axis=-1)
    return np.dot(gridout, [b1, b2])


def h_square2d(k, t):
    return (
        -2
        * t
        * (
            np.cos(k[..., 0, np.newaxis, np.newaxis])
            + np.cos(k[..., 1, np.newaxis, np.newaxis])
        )
        * np.eye(ed.Norb)
    )


def test_dos(hk, plot=False):
    result = np.histogram(
        hk[:, 0, 0], bins=100, density=True
    )  # normalized to one, I will have to multiply
    dx = result[1][2] - result[1][1]
    np.savetxt(
        "dos.dat",
        np.transpose(
            [np.delete(np.add(result[1], dx / 2), np.size(result[1]) - 1), result[0]]
        ),
    )

    if plot:
        plt.xlabel("E")
        plt.ylabel("D(E)")
        plt.xlim(-3, 3)
        plt.ylim(0, 1)
        plt.plot(
            np.delete(np.add(result[1], dx / 2), np.size(result[1]) - 1), result[0]
        )
        plt.show()


# READ ED INPUT:
ed.read_input("inputAHM.conf")


# Parameters
wmixing = 0.5
try:
    Nk = int(sys.argv[1])
except:
    Nk = 30

print(ed.Uloc)
t_hop = 0.25

# BUILD frequency arrays and k grid:
wm = np.pi / ed.beta * (2 * np.arange(ed.Lmats) + 1)
wr = np.linspace(ed.wini, ed.wfin, ed.Lreal, dtype=complex)

kgrid = generate_kgrid(Nk)


# Generate hk and hloc
Hk = h_square2d(kgrid, t_hop)
HkNambu = np.array([h_square2d(kgrid, t_hop), -np.conj(h_square2d(-kgrid, t_hop))])
Hloc = np.sum(Hk, axis=0) / Nk**2
Hloc = Hloc.astype(complex)


# Generate dos and plot it
test_dos(Hk)

# SETUP SOLVER
ed.set_hloc(Hloc)
Nb = ed.get_bath_dimension()
bath = ed.init_solver()
bath_prev = np.copy(bath)


# DMFT CYCLE
converged = False
iloop = 0
while not converged and iloop < ed.Nloop:
    iloop = iloop + 1
    print("DMFT-loop:", iloop, "/", ed.Nloop)

    ed.solve(bath)

    Smats = np.array([ed.get_sigma(axis="m", typ="n"), ed.get_sigma(axis="m", typ="a")])
    Sreal = np.array(
        [
            ed.build_sigma(wr + 1j * ed.eps, typ="n"),
            ed.build_sigma(wr + 1j * ed.eps, typ="a"),
        ]
    )

    Gmats = get_gloc(wm * 1j, ed.xmu, HkNambu, Smats, axis="m")
    Greal = get_gloc(wr + 1j * ed.eps, ed.xmu, HkNambu, Sreal, axis="r")
    Weiss = get_weiss_field(Gmats, Smats)

    # Print

    if rank == 0:
        for ispin in range(ed.Nspin):
            for iorb in range(ed.Norb):
                io = iorb + ed.Norb * ispin
                for typ in ["G", "F"]:
                    for axis in ["i", "real"]:
                        name = (
                            typ
                            + "_l"
                            + str(iorb + 1)
                            + "_s"
                            + str(ispin + 1)
                            + "_"
                            + axis
                            + "w.dat"
                        )
                        comp = 0 if typ == "G" else 1
                        Grfx = Gmats if axis == "i" else Greal
                        freq = wm if axis == "i" else np.real(wr)
                        np.savetxt(
                            name,
                            np.transpose(
                                [
                                    freq,
                                    Grfx[comp, io, io, :].imag,
                                    Grfx[comp, io, io, :].real,
                                ]
                            ),
                        )

    # Fit
    bath = ed.chi2_fitgf(Weiss[0], Weiss[1], bath)

    if iloop > 1:
        bath = wmixing * bath + (1.0 - wmixing) * bath_prev
    bath_prev = np.copy(bath)

    err, converged = ed.check_convergence(Weiss, ed.dmft_error)

ed.finalize_solver()
print("Done...")
