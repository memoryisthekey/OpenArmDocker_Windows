FROM osrf/ros:humble-desktop

SHELL ["/bin/bash", "-lc"]
ENV DEBIAN_FRONTEND=noninteractive

# =========================
# User configuration (CHANGE HERE)
# =========================
ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=1000

# =========================
# Base tools
# =========================
RUN apt-get update && apt-get install -y \
    sudo \
    git \
    nano \
    rsync \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    software-properties-common \
  && rm -rf /var/lib/apt/lists/*

# =========================
# Create normal user
# =========================
RUN groupadd --gid ${USER_GID} ${USERNAME} && \
    useradd --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/bash ${USERNAME} && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} && \
    chmod 0440 /etc/sudoers.d/${USERNAME}

# =========================
# SocketCAN tools
# =========================
RUN apt-get update && \
    add-apt-repository -y ppa:openarm/main && \
    apt-get update && \
    apt-get install -y \
      can-utils \
      iproute2 \
      libopenarm-can-dev \
      openarm-can-utils \
    && rm -rf /var/lib/apt/lists/*

# =========================
# ROS Control + MoveIt deps
# =========================
RUN apt-get update && apt-get install -y \
  ros-humble-controller-manager \
  ros-humble-gripper-controllers \
  ros-humble-hardware-interface \
  ros-humble-joint-state-broadcaster \
  ros-humble-joint-trajectory-controller \
  ros-humble-forward-command-controller \
  ros-humble-moveit-configs-utils \
  ros-humble-moveit-planners \
  ros-humble-moveit-ros-move-group \
  ros-humble-moveit-ros-visualization \
  ros-humble-moveit-simple-controller-manager \
  python3-flake8-docstrings \
  python3-pytest-cov \
  ros-dev-tools \
  && rm -rf /var/lib/apt/lists/*

# =========================
# Workspace
# =========================
ENV ROS_WS=/home/${USERNAME}/ros2_ws

RUN mkdir -p ${ROS_WS}/src && \
    chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}

# Source ROS automatically
RUN echo "source /opt/ros/humble/setup.bash" >> /home/${USERNAME}/.bashrc

# Switch to user
USER ${USERNAME}
WORKDIR ${ROS_WS}

# =========================
# Clone + build OpenARM
# =========================
#RUN cd src && \
#    git clone https://github.com/enactic/openarm_ros2.git && \
#    git clone https://github.com/enactic/openarm_description.git && \
#    cd .. && \
#    source /opt/ros/humble/setup.bash && \
#    colcon build 
#
#
## Source workspace overlay
RUN echo "source ${ROS_WS}/install/setup.bash" >> /home/${USERNAME}/.bashrc

CMD ["bash"]