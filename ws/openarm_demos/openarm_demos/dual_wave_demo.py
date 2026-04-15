#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint


class DualWaveDemo(Node):
    def __init__(self):
        super().__init__("dual_wave_demo")

        self.left_client = ActionClient(
            self,
            FollowJointTrajectory,
            "/left_joint_trajectory_controller/follow_joint_trajectory",
        )
        self.right_client = ActionClient(
            self,
            FollowJointTrajectory,
            "/right_joint_trajectory_controller/follow_joint_trajectory",
        )

        self.left_done = False
        self.right_done = False

        # Default speed scale for demo 20% of the original speed.
        self.declare_parameter("speed", 0.2)
        self.speed_scale = self.get_parameter("speed").value

        if self.speed_scale <= 0.0 or self.speed_scale > 1.5:
            self.get_logger().error("speed must be > 0.0 and <= 1.5")
            raise ValueError("speed must be > 0.0 and <= 1.5")

        self.get_logger().info(f"Using speed={self.speed_scale} \n To change the speed use: --ros-args -p speed:= <value between 0.0 and 1.5>")

        self.left_joint_names = [
            "openarm_left_joint1",
            "openarm_left_joint2",
            "openarm_left_joint3",
            "openarm_left_joint4",
            "openarm_left_joint5",
            "openarm_left_joint6",
            "openarm_left_joint7",
        ]

        self.right_joint_names = [
            "openarm_right_joint1",
            "openarm_right_joint2",
            "openarm_right_joint3",
            "openarm_right_joint4",
            "openarm_right_joint5",
            "openarm_right_joint6",
            "openarm_right_joint7",
        ]

        self.get_logger().info("Waiting for left controller...")
        self.left_client.wait_for_server()
        self.get_logger().info("Waiting for right controller...")
        self.right_client.wait_for_server()
        self.get_logger().info("Both controllers are ready.")

        self.send_goals()

    def make_point(self, positions, t_sec):
        p = JointTrajectoryPoint()
        p.positions = positions
        p.velocities = [0.0] * len(positions)
        
        #Scaling time to complete the trajectory slower:
        t_sec = t_sec / self.speed_scale
        p.time_from_start.sec = int(t_sec)
        p.time_from_start.nanosec = int((t_sec - int(t_sec)) * 1e9)
        return p

    def build_left_goal(self):
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = self.left_joint_names

        home = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        # From RViz test:
        # j1=-69°, j2=-63°, j3=0°, j4=72°, j5=90°, j6=3°, j7=0°
        greet = [-1.20, -1.10, 0.0, 1.26, 1.57, 0.05, 0.0]
        wave_a = [-1.20, -1.10, 0.0, 1.00, 1.57, 0.05, 0.0]
        wave_b = [-1.20, -1.10, 0.0, 1.50, 1.57, 0.05, 0.0]

        goal.trajectory.points = [
            self.make_point(home, 1.0),
            self.make_point(greet, 4.0),
            self.make_point(wave_a, 5.0),
            self.make_point(wave_b, 6.0),
            self.make_point(wave_a, 7.0),
            self.make_point(wave_b, 8.0),
            self.make_point(home, 10.0),
        ]
        return goal

    def build_right_goal(self):
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = self.right_joint_names

        home = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        # From RViz test:
        # j1=82°, j2=61°, j3=0°, j4=72°, j5=90°, j6=3°, j7=0°
        greet = [1.43, 1.06, 0.0, 1.26, 1.57, 0.05, 0.0]
        wave_a = [1.43, 1.06, 0.0, 1.00, 1.57, 0.05, 0.0]
        wave_b = [1.43, 1.06, 0.0, 1.50, 1.57, 0.05, 0.0]

        goal.trajectory.points = [
            self.make_point(home, 1.0),
            self.make_point(greet, 4.0),
            self.make_point(wave_a, 5.0),
            self.make_point(wave_b, 6.0),
            self.make_point(wave_a, 7.0),
            self.make_point(wave_b, 8.0),
            self.make_point(home, 10.0),
        ]
        return goal

    def send_goals(self):
        left_goal = self.build_left_goal()
        right_goal = self.build_right_goal()

        self.get_logger().info("Sending both arm trajectories...")
        self.left_client.send_goal_async(left_goal).add_done_callback(
            self.left_goal_response_callback
        )
        self.right_client.send_goal_async(right_goal).add_done_callback(
            self.right_goal_response_callback
        )

    def left_goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Left goal rejected.")
            self.left_done = True
            self.check_done()
            return

        self.get_logger().info("Left goal accepted.")
        goal_handle.get_result_async().add_done_callback(self.left_result_callback)

    def right_goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Right goal rejected.")
            self.right_done = True
            self.check_done()
            return

        self.get_logger().info("Right goal accepted.")
        goal_handle.get_result_async().add_done_callback(self.right_result_callback)

    def left_result_callback(self, future):
        self.get_logger().info("Left trajectory finished.")
        self.left_done = True
        self.check_done()

    def right_result_callback(self, future):
        self.get_logger().info("Right trajectory finished.")
        self.right_done = True
        self.check_done()

    def check_done(self):
        if self.left_done and self.right_done:
            self.get_logger().info("Both trajectories finished.")
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = DualWaveDemo()
    rclpy.spin(node)


if __name__ == "__main__":
    main()