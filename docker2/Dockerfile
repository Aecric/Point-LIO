# syntax=docker/dockerfile:1.6
# ============================================================================
# Lightning-LM ROS2 Humble .deb 打包 Dockerfile (x86 宿主模拟 ARM64 目标)
#
# 构建目标: Jetson NX (Ubuntu 22.04, ARM64)
# 构建环境: x86_64 宿主 + QEMU 用户态模拟
#
# 使用方式: 见配套的 build.sh
# ============================================================================

# ---------------------------------------------------------------------------
# Stage 1: builder - 下载依赖、编译、打包
# ---------------------------------------------------------------------------
FROM ros:humble-perception AS builder

ARG TARGETARCH
# QEMU 模拟下并发数要保守,默认 2; 宿主内存充足可通过 --build-arg 调到 4
ARG BUILD_JOBS=2

ENV ROS_WS=/root/slam_ws \
    DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8

# ---------------------------------------------------------------------------
# 1. 切换到 USTC 镜像源 (ARM64 用 ubuntu-ports)
# ---------------------------------------------------------------------------
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        REPO="mirrors.ustc.edu.cn/ubuntu-ports"; \
    else \
        REPO="mirrors.ustc.edu.cn/ubuntu"; \
    fi && \
    printf "deb https://$REPO/ jammy main restricted universe multiverse\n\
deb-src https://$REPO/ jammy main restricted universe multiverse\n\
deb https://$REPO/ jammy-updates main restricted universe multiverse\n\
deb-src https://$REPO/ jammy-updates main restricted universe multiverse\n\
deb https://$REPO/ jammy-security main restricted universe multiverse\n\
deb-src https://$REPO/ jammy-security main restricted universe multiverse\n" > /etc/apt/sources.list

# ---------------------------------------------------------------------------
# 2. 安装编译依赖 + 打包工具
#    使用 BuildKit 缓存挂载加速 apt (即使被 QEMU 模拟, 下载也只做一次)
# ---------------------------------------------------------------------------
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,id=apt-cache-arm64 \
    --mount=type=cache,target=/var/lib/apt,sharing=locked,id=apt-lib-arm64 \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        cmake make g++ gcc libssl-dev libboost-all-dev libeigen3-dev \
        libpcl-dev libgoogle-glog-dev libopencv-dev libyaml-cpp-dev \
        libgflags-dev liboctomap-dev libassimp-dev liburdfdom-dev \
        python3-pip python3-bloom python3-rosdep \
        fakeroot debhelper dpkg-dev devscripts equivs lsb-release \
        ros-${ROS_DISTRO}-pcl-conversions ros-${ROS_DISTRO}-pcl-ros \
        ros-${ROS_DISTRO}-octomap ros-${ROS_DISTRO}-pinocchio \
        zip ca-certificates \
        libepoxy-dev libgl1-mesa-dev libgles2-mesa-dev libegl1-mesa-dev \
        libx11-dev libwayland-dev libxkbcommon-dev libopengl-dev libegl-dev

# ---------------------------------------------------------------------------
# 3. 初始化 rosdep (放在 COPY 之前, 充分利用层缓存)
# ---------------------------------------------------------------------------
RUN rosdep init 2>/dev/null || true && \
    rosdep update --rosdistro=${ROS_DISTRO}

# ---------------------------------------------------------------------------
# 4. 拷贝源码 (依赖根目录的 .dockerignore 过滤 build/.git 等)
# ---------------------------------------------------------------------------
WORKDIR ${ROS_WS}/src/Point-LIO
COPY . .

# ---------------------------------------------------------------------------
# 5. 生成 debian 配置并构建 .deb
#
#    QEMU 模拟下的关键注意:
#    - 并发数用 ARG BUILD_JOBS 显式控制, 不要用 $(nproc)
#      ($(nproc) 在 QEMU 里返回宿主核数, 会吃爆内存)
#    - sed 注入 -DUSE_UI=OFF, 保留 bloom 原有的 /opt/ros/humble 前缀
# ---------------------------------------------------------------------------
RUN /bin/bash -c "set -eo pipefail && \
    source /opt/ros/${ROS_DISTRO}/setup.bash && \
    set -u && \
    \
    bloom-generate rosdebian \
        --os-name ubuntu \
        --os-version jammy \
        --ros-distro ${ROS_DISTRO} && \
    \
    sed -i 's|dh_auto_configure --|dh_auto_configure -- -DUSE_UI=OFF|' debian/rules && \
    printf '\noverride_dh_usrlocal:\n\ttrue\n' >> debian/rules && \
    \
    echo '===== debian/rules (key sections) =====' && \
    grep -A3 'override_dh_auto_configure\|override_dh_usrlocal' debian/rules && \
    echo '=======================================' && \
    \
    export DEB_BUILD_OPTIONS=parallel=${BUILD_JOBS} && \
    echo \"Building with DEB_BUILD_OPTIONS=\$DEB_BUILD_OPTIONS\" && \
    \
    fakeroot debian/rules binary"

# 把生成的 .deb 收集到固定位置, 方便后续导出
RUN mkdir -p /output && \
    cp ${ROS_WS}/src/*.deb /output/ && \
    ls -lh /output/

# ---------------------------------------------------------------------------
# Stage 2: export - 只包含 .deb, 用于 --output type=local 直接导出文件
# ---------------------------------------------------------------------------
FROM scratch AS export
COPY --from=builder /output/*.deb /