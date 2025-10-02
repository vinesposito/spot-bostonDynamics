# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Esempio robusto di utilizzo dell'AudioVisual Service, che include controlli di sicurezza,
gestione del lease, accensione e spegnimento del robot.
"""
import argparse
import os
import sys
import time

from google.protobuf.duration_pb2 import Duration

# Assicurati che questi import siano presenti in cima al file
import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import audio_visual_pb2, estop_pb2
from bosdyn.api.spot import choreography_params_pb2
from bosdyn.client.audio_visual import AudioVisualClient
from bosdyn.client.estop import EstopClient
from bosdyn.client.robot_command import RobotCommandClient, blocking_stand


def verify_estop(robot):
    """Verifica che il robot non sia in stato di E-Stop."""
    client = robot.ensure_client(EstopClient.default_service_name)
    if client.get_status().stop_level != estop_pb2.ESTOP_LEVEL_NONE:
        error_message = "ERRORE: Il robot è in stato di E-Stop. Rilasciare l'E-Stop prima di continuare."
        robot.logger.error(error_message)
        raise Exception(error_message)
    robot.logger.info("Verifica E-Stop superata.")


# Rimuovi l'import di choreography_params_pb2 dagli import in cima al file!

def run_robust_scale(config):
    """
    Esegue una sequenza di note e colori, gestendo l'intero ciclo di vita del comando
    in modo sicuro e robusto.
    """
    # Setup standard dell'SDK e connessione al robot
    bosdyn.client.util.setup_logging(config.verbose)
    sdk = bosdyn.client.create_standard_sdk('RobustScalaMusicaleClient', [AudioVisualClient])
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    # Fase 1: Controlli di Sicurezza Preliminari
    verify_estop(robot)

    # Ottenimento di tutti i client necessari
    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    command_client = robot.ensure_client(RobotCommandClient.default_service_name)
    av_client = robot.ensure_client(AudioVisualClient.default_service_name)

    # Il blocco finally garantisce che lo spegnimento venga tentato anche in caso di errore
    try:
        # Fase 2: Acquisizione del Controllo e Preparazione
        with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
            robot.logger.info("Lease acquisito.")

            robot.logger.info("Accensione dei motori in corso...")
            robot.power_on(timeout_sec=20)
            assert robot.is_powered_on(), "Accensione del robot fallita."
            robot.logger.info("Robot acceso.")

            robot.logger.info("Comando di stand-up...")
            blocking_stand(command_client, timeout_sec=10)
            robot.logger.info("Robot in piedi e pronto.")

            volume_desiderato = 0.5
            robot.logger.info(f"Impostazione del volume massimo del buzzer a {volume_desiderato * 100}%...")
            av_client.set_system_params(enabled=True, buzzer_max_volume=volume_desiderato)

            # Fase 3: Esecuzione della Logica Principale (La Scala)
            robot.logger.info("Inizio della sequenza audio-visuale...")

            existing_behaviors = av_client.list_behaviors()
            priority = max([b.behavior.priority for b in existing_behaviors] or [0]) + 1
            robot.logger.info(f"Utilizzo della priorità: {priority}")

            # ############################################################### #
            # ##          RIPRISTINO DELLA DEFINIZIONE CORRETTA              ## #
            # ############################################################### #
            scala = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"]
            note_map = {
                "Do": choreography_params_pb2.BuzzerNoteParams.Note.NOTE_C,
                "Re": choreography_params_pb2.BuzzerNoteParams.Note.NOTE_D,
                "Mi": choreography_params_pb2.BuzzerNoteParams.Note.NOTE_E,
                "Fa": choreography_params_pb2.BuzzerNoteParams.Note.NOTE_F,
                "Sol": choreography_params_pb2.BuzzerNoteParams.Note.NOTE_G,
                "La": choreography_params_pb2.BuzzerNoteParams.Note.NOTE_A,
                "Si": choreography_params_pb2.BuzzerNoteParams.Note.NOTE_B,
            }
            colori_rgb = [(255, 0, 0), (255, 128, 0), (255, 255, 0), (0, 255, 0),
                          (0, 255, 255), (0, 0, 255), (127, 0, 255)]
            durata_nota_sec = config.durata_nota
            durata_nota_proto = Duration(seconds=int(durata_nota_sec), nanos=int((durata_nota_sec % 1) * 1e9))

            for i, nome_nota in enumerate(scala):
                nota_enum = note_map[nome_nota]
                colore_rgb = colori_rgb[i]
                behavior_name = f"nota_{nome_nota.lower()}"

                robot.logger.info(f"Preparazione: {nome_nota} con colore {colore_rgb}")

                colore_proto = audio_visual_pb2.Color(
                    rgb=audio_visual_pb2.Color.RGB(r=colore_rgb[0], g=colore_rgb[1], b=colore_rgb[2]))

                led_sequence = audio_visual_pb2.LedSequenceGroup.LedSequence(
                    solid_color_sequence=audio_visual_pb2.LedSequenceGroup.LedSequence.SolidColorSequence(
                        color=colore_proto))
                led_group = audio_visual_pb2.LedSequenceGroup(front_center=led_sequence, front_left=led_sequence,
                                                              front_right=led_sequence, hind_left=led_sequence,
                                                              hind_right=led_sequence)

                # Ripristiniamo anche la struttura annidata, ma manteniamo 'octave=4' semplice
                nota_con_durata = audio_visual_pb2.AudioSequenceGroup.BuzzerSequence.NoteWithDuration(
                    note=choreography_params_pb2.BuzzerNoteParams(note=nota_enum, octave=4),
                    duration=durata_nota_proto)

                buzzer_sequence = audio_visual_pb2.AudioSequenceGroup.BuzzerSequence()
                buzzer_sequence.notes.append(nota_con_durata)
                audio_group = audio_visual_pb2.AudioSequenceGroup(buzzer=buzzer_sequence)

                behavior = audio_visual_pb2.AudioVisualBehavior(enabled=True, priority=priority,
                                                                led_sequence_group=led_group,
                                                                audio_sequence_group=audio_group)

                try:
                    av_client.add_or_modify_behavior(name=behavior_name, behavior=behavior)
                    end_time = time.time() + durata_nota_sec
                    av_client.run_behavior(behavior_name, end_time)
                    time.sleep(durata_nota_sec)
                finally:
                    av_client.delete_behaviors([behavior_name])

            robot.logger.info("Sequenza audio-visuale completata con successo.")

    finally:
        # Fase 4: Spegnimento Sicuro (Blocco finally)
        robot.logger.info("Inizio procedura di spegnimento sicuro...")
        if robot.is_powered_on():
            robot.power_off(cut_immediately=False, timeout_sec=20)
            assert not robot.is_powered_on(), "Spegnimento del robot fallito."
            robot.logger.info("Robot spento in modo sicuro.")
        else:
            robot.logger.info("Il robot non era acceso, nessuna azione di spegnimento necessaria.")

def main():
    """Interfaccia a riga di comando."""
    parser = argparse.ArgumentParser(description=run_robust_scale.__doc__)
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('-d', '--durata-nota', type=float, default=0.7,
                        help='Durata di ogni nota in secondi.')

    # ################################################################### #
    # ##                   QUI È LA MODIFICA CHIAVE                      ## #
    # ################################################################### #

    # 1. Controlliamo se la variabile d'ambiente per l'hostname è impostata.
    hostname_from_env = os.getenv('BOSDYN_CLIENT_HOSTNAME')

    # 2. Se la variabile esiste, modifichiamo l'argomento 'hostname' nel parser
    #    per renderlo opzionale e dargli come valore predefinito quello
    #    della variabile d'ambiente.
    if hostname_from_env:
        for action in parser._actions:
            if action.dest == 'hostname':
                action.nargs = '?'  # Rende l'argomento posizionale opzionale
                action.default = hostname_from_env

    # Ora, quando chiamiamo parse_args(), non darà errore se l'hostname non
    # è sulla riga di comando, perché userà il valore di default che abbiamo appena impostato.
    options = parser.parse_args()

    # #################### FINE DELLA MODIFICA ########################### #

    try:
        run_robust_scale(options)
        return True
    except Exception as exc:
        logger = bosdyn.client.util.get_logger()
        logger.error("Esecuzione dello script fallita: %s", exc)
        return False


if __name__ == '__main__':
    if not main():
        sys.exit(1)