from threading import Condition, Thread
import time

cond = Condition()
shared_var = 0


class Producer(Thread):
    def run(self):
        global shared_var
        while True:
            with cond:
                shared_var += 1
                print("produced")
                cond.notify()
            time.sleep(1)


class Consumer(Thread):
    def run(self):
        global shared_var
        while True:
            with cond:
                while shared_var:
                    cond.wait()

                shared_var -= 1
                print("consumed")
            time.sleep(1)


if __name__ == "__main__":
    p = Producer()
    c = Consumer()
    c.start()
    time.sleep(2)
    p.start()
    
    p.join()
    c.join()
