import signal
import threading
import time


def do_some_work(n_iter):
    for i in range(n_iter):
        if stop_event.is_set():
            break
        print(f'iteration {i + 1}/{n_iter}')
        time.sleep(0.5)
    print('Thread done')


def handle_kb_interrupt(sig, frame):
    stop_event.set()


if __name__ == '__main__':
    stop_event = threading.Event()
    signal.signal(signal.SIGINT, handle_kb_interrupt)    
    n_iter = 100
    thread = threading.Thread(target=do_some_work, args=(n_iter,))
    thread.start()
    thread.join()
    print('Program done')