'''
GUI for the Pi-chain
'''
import PySimpleGUI as sg
import subprocess
import sys
from node import Node


def main():
    app_node = Node()
    # app_node.pretty_data()

    col_1 = [
        [sg.Button('Start Event Listener')],
        [sg.Button('Start Miner')],
        [sg.Button('Stop Miner')],
        [sg.Button('Stop Event Listener')],
        [sg.Button('Close Pi-Chain')]
    ]

    col_2 = [
        [sg.Button('Display Data')],
        [sg.Button('Display Chain')],
        [sg.Button('Display Last Block')],
        [sg.Button('Display Transactions')],
        [sg.Button('Connect to Network')]
    ]

    col_3 = [
        [sg.Button('Generate Transaction')],
        [sg.Button('Show Ledger')]
    ]

    node_layout = [
        [sg.Column(col_1), sg.Column(col_2), sg.Column(col_3)],
        [sg.Multiline("", size=(50, 50), key='OUTPUT'), sg.Multiline("", size=(50, 50), key='DATA'),
         sg.Output(size=(50, 50))]
    ]

    window = sg.Window('Pi-Chain Node', layout=node_layout, default_element_size=(380, 250), resizable=True)

    while True:
        event, values = window.read()
        if event == 'Start Event Listener':
            app_node.start_event_listener()
        elif event == 'Stop Event Listener':
            app_node.stop_event_listener()
        elif event == 'Start Miner':
            app_node.start_miner()
        elif event == 'Stop Miner':
            app_node.stop_miner()
        elif event == 'Display Data':
            app_node.pretty_data()
            temp_val = "Test1 \r\nTest2"
            window['OUTPUT'].update(value=temp_val)
        elif event == 'Display Chain':
            app_node.pretty_chain()
        elif event == 'Display Last Block':
            app_node.pretty_last_block()
        elif event == 'Display Transactions':
            app_node.pretty_transactions()
        elif event == 'Connect to Network':
            app_node.connect_to_network(app_node.MAIN_NODE)
        elif event == 'Generate Transaction':
            app_node.generate_transactions()
        elif event == 'Show Ledger':
            print(app_node.ledger)
        elif event in ['Close Pi-Chain', sg.WIN_CLOSED]:
            app_node.stop_event_listener()
            while app_node.is_listening:
                pass
            break

    window.close()


if __name__ == "__main__":
    main()
