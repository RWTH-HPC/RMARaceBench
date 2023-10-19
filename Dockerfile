FROM debian:12

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Berlin

RUN apt-get update \
    && apt-get -y -qq --no-install-recommends install \
    cmake \
    curl \
    binutils-dev \
    make \
    automake \
    autotools-dev \
    autoconf \
    libtool \
    zlib1g \
    zlib1g-dev \
    libatomic1 \
    libfabric-dev \
    libxml2-dev \
    python3 \
    python3-pip \
    python3-venv \
    gfortran \
    gcc \
    g++ \
    git \
    graphviz \
    libgtest-dev \
    clang-15 \
    libomp-15-dev \
    clang-format-15 \
    llvm-15 \
    lldb-15 \
    ninja-build \
    vim \
    openssh-client \
    gdb \
    wget \
    googletest \
    && apt-get -yq clean \
    && rm --recursive --force /var/lib/apt/lists/*

# Install OpenMPI
RUN apt-get update \
    && apt-get -y -qq --no-install-recommends install \
    openmpi-bin \
    libopenmpi-dev \
    && apt-get -yq clean \
    && rm --recursive --force /var/lib/apt/lists/*

# Delete shmem headers from OpenMPI installation that could conflict with OpenSHMEM
RUN rm /usr/lib/x86_64-linux-gnu/openmpi/include/shmem.h && \
    rm /usr/lib/x86_64-linux-gnu/openmpi/include/pshmem.h && \
    rm /usr/lib/x86_64-linux-gnu/openmpi/include/shmem.fh && \
    rm /usr/lib/x86_64-linux-gnu/openmpi/include/shmemx.h && \
    rm /usr/lib/x86_64-linux-gnu/openmpi/include/pshmemx.h && \
    rm /usr/lib/x86_64-linux-gnu/openmpi/include/shmem-compat.h


# ensure that LLVM 15 toolset is used
RUN ln -s /usr/bin/FileCheck-15 /usr/bin/FileCheck
RUN ln -s /usr/bin/clang-15 /usr/bin/clang
RUN ln -s /usr/bin/clang++-15 /usr/bin/clang++
RUN ln -s /usr/bin/clang-format-15 /usr/bin/clang-format

# Install Python dependencies and ensure to activate virtualenv (by setting PATH variable)
COPY requirements.txt .
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip3 install --no-input --no-cache-dir --disable-pip-version-check -r /requirements.txt

WORKDIR /externals

# Install OpenSHMEM
RUN     wget https://github.com/Sandia-OpenSHMEM/SOS/archive/refs/tags/v1.5.1.tar.gz -O SOS-1.5.1.tar.gz && \
        tar -xf SOS-1.5.1.tar.gz && \
        cd SOS-1.5.1 && \
        ./autogen.sh && \
        OMPI_CC=clang OMPI_CXX=clang++ MPICH_CC=clang MPICH_CXX=clang++ CC=mpicc CXX=mpicxx ./configure --prefix=/usr --with-ofi=/usr --enable-pmi-mpi --disable-cxx --disable-fortran --enable-error-checking --enable-profiling=yes && \
        make -j$(nproc) install

# Install GPI (GASPI)
RUN    wget https://github.com/cc-hpc-itwm/GPI-2/archive/refs/tags/v1.5.1.tar.gz -O GPI-2-1.5.1.tar.gz && \
       tar -xf GPI-2-1.5.1.tar.gz && \
       cd GPI-2-1.5.1 && \
       ./autogen.sh && \
       OMPI_CC=clang OMPI_CXX=clang++ MPICH_CC=clang MPICH_CXX=clang++ CC=mpicc CXX=mpicxx ./configure --prefix=/usr --with-mpi --with-infiniband=no --with-ethernet --with-pbs=no && \
       make -j$(nproc) install

# Install PARCOACH
RUN   wget https://gitlab.inria.fr/parcoach/parcoach/-/archive/2.3.1/parcoach-2.3.1.tar.gz && \
      tar -xf parcoach-2.3.1.tar.gz && \
      cd parcoach-2.3.1 && \
      mkdir -p build && \
      cd build && \
      CC=clang CXX=clang++ OMPI_CC=clang OMPI_CXX=clang++ MPICH_CC=clang MPICH_CXX=clang++ cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/parcoach -DPARCOACH_ENABLE_TESTS=OFF .. && \
      make -j$(nproc) install


# Install MUST
RUN wget https://hpc.rwth-aachen.de/must/files/MUST-v1.9.0-rma.tar.gz && \
    tar -xf MUST-v1.9.0-rma.tar.gz && \
    cd MUST-v1.9.0-rma && \
    mkdir -p build && \
    cd build && \
    CC=clang CXX=clang++ OMPI_CC=clang OMPI_CXX=clang++ MPICH_CC=clang MPICH_CXX=clang++ cmake -DCMAKE_BUILD_TYPE=Release -DUSE_BACKWARD=ON -DENABLE_FORTRAN=OFF -DENABLE_TYPEART=OFF -DCMAKE_INSTALL_PREFIX=/opt/must .. && \
    make -j$(nproc) install && \
    make -j$(nproc) -j32 install-prebuilds

# Clean up externals
RUN rm -rf /externals

WORKDIR /

# Run script
COPY MPIRMA /rmaracebench/MPIRMA
COPY SHMEM /rmaracebench/SHMEM
COPY GASPI /rmaracebench/GASPI
COPY templates /rmaracebench/templates
COPY util/run_test.py /rmaracebench/run_test.py
COPY util/parse_results.py /rmaracebench/parse_results.py
COPY util/generate.py /rmaracebench/generate.py

# Allow oversubscription for OpenMPI
ENV OMPI_MCA_rmaps_base_oversubscribe=1

# Run as non-privileged user
RUN     useradd -ms /bin/bash user
RUN chown -R user:user /rmaracebench
USER user

ENV OMPI_CC=clang
ENV OMPI_CXX=clang++
ENV MPICH_CC=clang
ENV MPICH_CXX=clang++
ENV PATH="/opt/must/bin:/opt/parcoach/bin:$PATH"

WORKDIR /rmaracebench