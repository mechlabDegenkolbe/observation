#!/usr/bin/env python
'''
Created on 04.06.2015

@author: kolbe
'''
import cv2
import numpy as np
import time
import sys
import socket
from optparse import OptionParser

cap = None

def get_frame():
    ret, frame = cap.read()
    
    if not ret:
        return ret, None, None
    
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    return ret, frame, frame_gray
    

if __name__ == '__main__':
    
    parser = OptionParser()
    parser.add_option("-c", "--cam", dest="camera",
                  help="Camera number", default=0, type="int")
    parser.add_option("-d", "--directory", dest="directory",
                      help="Directory where images will be saved", default="./")
    parser.add_option("-w", "--window", dest="window",
                      help="Show windows", action="store_true")
    parser.add_option("-o", "--stdout", dest="out",
                      help="Write images to stdout", action="store_true")
    parser.add_option("-n", "--network", dest="network",
                      help="Write images to ip:port")       

    (options, args) = parser.parse_args()
    
    alpha = 0.01
    videoinput = options.camera
    
    # if network
    sock = None
    if options.network:
        ip, port = options.network.split(':')
        sock = socket.socket()
        print "trying to connect to ", options.network
        try:
            sock.connect((ip, int(port)))
        except Exception, e:
            print "no connection %s" % str(e)
            sock = None
    
    ### window
    #cv2.namedWindow("path", cv2.WINDOW_OPENGL)
    if options.window:
        cv2.namedWindow("path", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("path", cv2.WND_PROP_FULLSCREEN, cv2.cv.CV_WINDOW_FULLSCREEN)
    
    ### capture
    global cap
    cap = cv2.VideoCapture(videoinput)
    ret, frame, frame_gray = get_frame()
    
    ### images
    average = np.float32(frame_gray)
    path_average = np.zeros(frame_gray.shape, np.float32)
    white = np.ones(frame_gray.shape, np.uint8)*255

    
    frame_nr = 1
    while ret:
        t0 = time.time()
        ### update running average
        cv2.accumulateWeighted(frame_gray, average, alpha)
        diff = cv2.absdiff(frame_gray, cv2.convertScaleAbs(average))
        ret, diff = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        if ret <= 5:
            diff = np.zeros(diff.shape, dtype=diff.dtype)
        
        if frame_nr > 20:
            cv2.accumulateWeighted(diff, path_average, 0.1)
            path = cv2.convertScaleAbs(path_average)
            path = cv2.subtract(white, path)
            
            #mat = cv2.getRotationMatrix2D((path.shape[1]/2, path.shape[0]/2), r.value(), 1.0)
            #path = cv2.warpAffine(path, mat, (path.shape[1], path.shape[0]))
  
            #cv2.imshow("frame", frame_gray)
            #cv2.imshow("diff", diff)
            if options.window:
                cv2.imshow("path", path)
                k = cv2.waitKey(1)
                if k == 27:
                    break
            if options.out:
                sys.stdout.write( path.tostring() )
            if sock is not None:
                encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]
                result, imgencode = cv2.imencode('.jpg', path, encode_param)
                data = np.array(imgencode)
                stringData = data.tostring()
                try:
                    sock.send( str(len(stringData)).ljust(16))
                    sock.send( stringData )
                except Exception, e:
                    print "Can't send image data to %s\n%s" % (options.network, e)
                
        
        ret, frame, frame_gray = get_frame()
        frame_nr += 1
        
        t_delta = time.time()-t0
        print "%dms" % (t_delta*1000), " %0.1ffps" % (1.0/t_delta), "size: ", frame_gray.shape[:2]
        