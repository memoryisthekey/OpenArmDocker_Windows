#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from control_msgs.action import FollowJointTrajectory, GripperCommand
from trajectory_msgs.msg import JointTrajectoryPoint


class HandshakeDemo(Node):
    def __init__(self):
        super().__init__("handshake_demo")

        self.done = False
        self.open_timer = None
        self.close_timer = None

        self.declare_parameter("speed", 0.5)
        self.declare_parameter("side", "right")

        requested_speed = float(self.get_parameter("speed").value)
        requested_side = str(self.get_parameter("side").value).lower()

        if requested_speed <= 0.0:
            self.get_logger().warn("speed must be > 0.0, using default 0.5")
            requested_speed = 0.5

        if requested_speed > 1.5:
            self.get_logger().warn(
                f"Requested speed {requested_speed} is too high, clamping to 1.5"
            )
            requested_speed = 1.5

        if requested_side not in ["left", "right"]:
            self.get_logger().warn(
                f"Invalid side '{requested_side}', using 'right'"
            )
            requested_side = "right"

        self.speed = requested_speed
        self.side = requested_side

        self.get_logger().info(f"Using speed={self.speed}")
        self.get_logger().info(f"Using side={self.side}")

        arm_action = f"/{self.side}_joint_trajectory_controller/follow_joint_trajectory"
        gripper_action = f"/{self.side}_gripper_controller/gripper_cmd"

        self.arm_client = ActionClient(
            self,
            FollowJointTrajectory,
            arm_action,
        )

        self.gripper_client = ActionClient(
            self,
            GripperCommand,
            gripper_action,
        )

        self.joint_names = [
            f"openarm_{self.side}_joint1",
            f"openarm_{self.side}_joint2",
            f"openarm_{self.side}_joint3",
            f"openarm_{self.side}_joint4",
            f"openarm_{self.side}_joint5",
            f"openarm_{self.side}_joint6",
            f"openarm_{self.side}_joint7",
        ]

        self.get_logger().info("Waiting for arm controller...")
        self.arm_client.wait_for_server()
        self.get_logger().info("Waiting for gripper controller...")
        self.gripper_client.wait_for_server()
        self.get_logger().info("Controllers are ready.")

        self.send_goal()

    def deg_list_to_rad(self, deg_list):
        return [math.radians(x) for x in deg_list]

    def make_point(self, positions, t_sec):
        p = JointTrajectoryPoint()
        p.positions = positions
        p.velocities = [0.0] * len(positions)

        t_sec = t_sec / self.speed
        p.time_from_start.sec = int(t_sec)
        p.time_from_start.nanosec = int((t_sec - int(t_sec)) * 1e9)
        return p

    def get_pose_degrees(self):
        # Right-arm reference poses from your screenshots
        right_first = [-7, 2, 1, 57, 3, 3, 30]
        right_up    = [-14, 1, 1, 73, 3, 2, 22]
        right_down  = [-4, 1, 0, 43, 2, 2, 51]

        if self.side == "right":
            return right_first, right_up, right_down

        # Mirrored first attempt for left arm
        left_first = [7, 2, 1, 57, 3, 3, -30]
        left_up    = [14, 1, 1, 73, 3, 2, -22]
        left_down  = [4, 1, 0, 43, 2, 2, -51]
        return left_first, left_up, left_down

    def build_goal(self):
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = self.joint_names

        home = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        first_deg, up_deg, down_deg = self.get_pose_degrees()

        first = self.deg_list_to_rad(first_deg)
        up = self.deg_list_to_rad(up_deg)
        down = self.deg_list_to_rad(down_deg)

        goal.trajectory.points = [
            self.make_point(home, 1.0),
            self.make_point(first, 4.0),
            self.make_point(up, 5.0),
            self.make_point(down, 6.0),
            self.make_point(up, 7.0),
            self.make_point(down, 8.0),
            self.make_point(first, 9.0),
            self.make_point(home, 11.0),
        ]
        return goal

    def send_gripper_command(self, position, max_effort=10.0):
        goal = GripperCommand.Goal()
        goal.command.position = position
        goal.command.max_effort = max_effort

        self.get_logger().info(
            f"Sending {self.side} gripper command: position={position}, max_effort={max_effort}"
        )
        self.gripper_client.send_goal_async(goal)

    def send_goal(self):
        goal = self.build_goal()

        self.get_logger().info(f"Sending {self.side} arm handshake trajectory...")
        self.arm_client.send_goal_async(goal).add_done_callback(
            self.goal_response_callback
        )

        open_time = 3.6 / self.speed
        self.open_timer = self.create_timer(open_time, self.open_gripper_once)

        close_time = 9.2 / self.speed
        self.close_timer = self.create_timer(close_time, self.close_gripper_once)

    def open_gripper_once(self):
        self.get_logger().info(f"Opening {self.side} gripper to 0.02")
        self.send_gripper_command(0.02)

        if self.open_timer is not None:
            self.open_timer.cancel()
            self.open_timer = None

    def close_gripper_once(self):
        self.get_logger().info(f"Closing {self.side} gripper")
        self.send_gripper_command(0.0)

        if self.close_timer is not None:
            self.close_timer.cancel()
            self.close_timer = None

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error(f"{self.side.capitalize()} goal rejected.")
            self.done = True
            self.check_done()
            return

        self.get_logger().info(f"{self.side.capitalize()} goal accepted.")
        goal_handle.get_result_async().add_done_callback(self.result_callback)

    def result_callback(self, future):
        self.get_logger().info(f"{self.side.capitalize()} trajectory finished.")
        self.done = True
        self.check_done()

    def check_done(self):
        if self.done:
            if self.open_timer is not None:
                self.open_timer.cancel()
                self.open_timer = None
            if self.close_timer is not None:
                self.close_timer.cancel()
                self.close_timer = None

            self.get_logger().info("Handshake finished.")
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = HandshakeDemo()
    rclpy.spin(node)


if __name__ == "__main__":
    main()