# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Script per comandare a Spot di accendersi, alzarsi, accendere i LED di verde,
attendere 3 secondi, e infine sedersi e spegnersi in sicurezza.
"""

import argparse
import sys
import time

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient, blocking_stand


def lights_routine(config):
    """Esegue la sequenza di comandi per Spot."""

    # Configura il logging
    bosdyn.client.util.setup_logging(config.verbose)

    # Crea l'oggetto SDK, il punto di ingresso principale per l'API
    sdk = bosdyn.client.create_standard_sdk('SpotLightsRoutineClient')

    # Crea l'oggetto robot specificando il suo hostname
    robot = sdk.create_robot(config.hostname)

    # Autentica il client con il robot
    bosdyn.client.util.authenticate(robot)

    # Stabilisce la sincronizzazione del tempo con il robot, necessaria per inviare comandi
    robot.time_sync.wait_for_sync()

    # Verifica che il robot non sia in stato di E-Stop
    assert not robot.is_estopped(), 'Robot is estopped. Please use an external E-Stop client.'

    # Ottiene il client per il lease. Solo un client alla volta può controllare il robot.
    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)

    # Il blocco 'with LeaseKeepAlive' gestisce automaticamente l'acquisizione e il rilascio del lease
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        # Ora siamo pronti ad accendere il robot.
        robot.logger.info('Accensione del robot in corso... Potrebbero volerci alcuni secondi.')
        robot.power_on(timeout_sec=20)
        assert robot.is_powered_on(), 'Accensione del robot fallita.'
        robot.logger.info('Robot acceso.')

        # Ottiene il client per inviare comandi al robot
        command_client = robot.ensure_client(RobotCommandClient.default_service_name)

        # 1. Comando per far alzare il robot (posizione di stand)
        robot.logger.info('Comando al robot: alzarsi...')
        blocking_stand(command_client, timeout_sec=10)
        robot.logger.info('Robot in posizione di stand.')
        time.sleep(1) # Piccola pausa

        # 2. Comando per accendere i LED di colore verde
        robot.logger.info('Accensione dei LED di colore verde...')
        # I valori RGB sono float da 0.0 a 1.0
        green_light_cmd = RobotCommandBuilder.led_command(red=0.0, green=1.0, blue=0.0)
        command_client.robot_command(green_light_cmd)

        # 3. Attesa di 3 secondi
        robot.logger.info('Attesa di 3 secondi...')
        time.sleep(3)

        # 4. NUOVA PARTE: Comando per cambiare i LED in colore BLU
        robot.logger.info('Cambio dei LED in colore blu...')
        blue_light_cmd = RobotCommandBuilder.led_command(red=0.0, green=0.0, blue=1.0)
        command_client.robot_command(blue_light_cmd)

        # 5. NUOVA PARTE: Attesa di altri 3 secondi
        robot.logger.info('Attesa di 3 secondi (luci blu)...')
        time.sleep(3)

        # Comando per spegnere i LED (impostandoli a nero)
        robot.logger.info('Spegnimento dei LED...')
        black_light_cmd = RobotCommandBuilder.led_command(red=0.0, green=0.0, blue=0.0)
        command_client.robot_command(black_light_cmd)
        time.sleep(1) # Piccola pausa

        # 4. & 5. Comando per spegnere il robot in sicurezza
        # Specificando 'cut_immediately=False', il robot proverà prima a sedersi.
        robot.logger.info('Comando al robot: sedersi e spegnersi in sicurezza...')
        robot.power_off(cut_immediately=False, timeout_sec=20)
        assert not robot.is_powered_on(), 'Spegnimento del robot fallito.'
        robot.logger.info('Robot spento in sicurezza.')


def main():
    """Interfaccia a riga di comando."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()
    try:
        lights_routine(options)
        return True
    except Exception as exc:
        logger = bosdyn.client.util.get_logger()
        logger.error('La routine ha generato un\'eccezione: %r', exc)
        return False


if __name__ == '__main__':
    if not main():
        sys.exit(1)