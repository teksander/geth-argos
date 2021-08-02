from aux import *
import time

import sched
s = sched.scheduler()

bufferRate = 0.25
ageLimit = 1

def Buffer(rate = bufferRate, ageLimit = ageLimit):
    """ Control routine for robot-to-robot dynamic peering """
    global peered

    def simplifiedBuffer():
        pass

    print('rate is', rate)
    # tic = TicToc(rate, 'Buffer')
    # while True: 
        
        # if not startFlag:
        #     gethEnodes = getEnodes()
        #     for enode in gethEnodes:
        #         w3.provider.make_request("admin_removePeer",[enode])
        #     mainlogger.info('Stopped Buffering')
        #     break



    # tic.tic()

    simplifiedBuffer()
    time.sleep(0.1)
    # tic.toc()


def run_buffer():

    s.enter(0.25, 1, Buffer)
    s.run()

while True:
    testtime = time.time()
    run_buffer()
    print(time.time()-testtime)


# bufferTh = threading.Thread(target=Buffer, args=())
# bufferTh.daemon = True         
 
# mainmodules = [bufferTh]

# bufferTh.start()
