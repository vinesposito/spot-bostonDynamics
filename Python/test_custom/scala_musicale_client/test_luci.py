# test_luci.py
import argparse
import os
import sys
import time

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import audio_visual_pb2, estop_pb2
from bosdyn.client.audio_visual import AudioVisualClient
from bosdyn.client.estop import EstopClient
from bosdyn.client.robot_command import RobotCommandClient, blocking_stand


def verify_estop(robot):
    """Verifica che il robot non sia in stato di E-Stop."""
    client = robot.ensure_client(EstopClient.default_service_name)
    if client.get_status().stop_level != estop_pb2.ESTOP_LEVEL_NONE:
        raise Exception("ERRORE: Il robot è in stato di E-Stop.")
    robot.logger.info("Verifica E-Stop superata.")


def test_luci(config):
    """Test minimo per accendere solo le luci."""
    bosdyn.client.util.setup_logging(config.verbose)
    sdk = bosdyn.client.create_standard_sdk('TestLuciClient', [AudioVisualClient])
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    verify_estop(robot)

    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    command_client = robot.ensure_client(RobotCommandClient.default_service_name)
    av_client = robot.ensure_client(AudioVisualClient.default_service_name)

    try:
        with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
            robot.logger.info("Lease acquisito.")
            robot.power_on(timeout_sec=20)
            robot.logger.info("Robot acceso.")
            blocking_stand(command_client, timeout_sec=10)
            robot.logger.info("Robot in piedi e pronto.")

            robot.logger.info("Inizio test solo luci...")

            behavior_name = "test_luce_rossa"
            priority = 100  # Usiamo una priorità alta per il test

            # Creiamo solo il comportamento per le luci
            colore_proto = audio_visual_pb2.Color(rgb=audio_visual_pb2.Color.RGB(r=255, g=0, b=0))
            led_sequence = audio_visual_pb2.LedSequenceGroup.LedSequence(
                solid_color_sequence=audio_visual_pb2.LedSequenceGroup.LedSequence.SolidColorSequence(
                    color=colore_proto)
            )
            led_group = audio_visual_pb2.LedSequenceGroup(
                front_center=led_sequence, front_left=led_sequence, front_right=led_sequence,
                hind_left=led_sequence, hind_right=led_sequence
            )

            # Il comportamento non ha nessuna parte audio
            behavior = audio_visual_pb2.AudioVisualBehavior(
                enabled=True, priority=priority, led_sequence_group=led_group
            )

            try:
                robot.logger.info(f"Caricamento comportamento '{behavior_name}'")
                av_client.add_or_modify_behavior(name=behavior_name, behavior=behavior)

                robot.logger.info(f"Esecuzione comportamento per 5 secondi...")
                end_time = time.time() + 5
                av_client.run_behavior(behavior_name, end_time)
                time.sleep(5)

                robot.logger.info("Test luci completato con successo.")
            finally:
                robot.logger.info("Cancellazione comportamento di test.")
                av_client.delete_behaviors([behavior_name])

    finally:
        robot.logger.info("Inizio procedura di spegnimento sicuro...")
        if robot.is_powered_on():
            robot.power_off(cut_immediately=False, timeout_sec=20)
            robot.logger.info("Robot spento in modo sicuro.")


def main():
    parser = argparse.ArgumentParser(description=test_luci.__doc__)
    bosdyn.client.util.add_base_arguments(parser)
    hostname_from_env = os.getenv('BOSDYN_CLIENT_HOSTNAME')
    if hostname_from_env:
        for action in parser._actions:
            if action.dest == 'hostname':
                action.nargs = '?'
                action.default = hostname_from_env
    options = parser.parse_args()

    try:
        test_luci(options)
        return True
    except Exception as exc:
        logger = bosdyn.client.util.get_logger()
        logger.error(f"Esecuzione dello script fallita: {exc}")
        return False


if __name__ == '__main__':
    if not main():
        sys.exit(1)