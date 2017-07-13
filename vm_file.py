#!/usr/bin/env python

import rospy
import sys
import time
import random


from gps_common.msg import GPSFix
from gps_common.msg import GPSStatus
from sensor_msgs.msg import NavSatFix

from std_msgs.msg import Float32
from std_msgs.msg import Int8
import sys
import cv2


def value_from_prop(prop, low, high):
    #runs the function y=mx+b where slope is m=(high-1ow)/2 and y-intercept is b=(low+high)/2
    return (((high-low)/2.0)*prop) + ((low+high)/2)
class Rudder:
    def __init__(self, min_angle, max_angle):
        self.RUDDER_PUB_TOPIC = "motor_cmd/steer"
        self.pub_rudder = rospy.Publisher(self.RUDDER_PUB_TOPIC, Int8, queue_size=1)
        self.max_angle = max_angle
        self.min_angle = min_angle
        self.angle = 0
        
    def set_angle(self, angle,comment = 0):
        if angle < self.min_angle:
            angle = self.min_angle
        elif angle > self.max_angle:
            angle = self.max_angle 
        if comment == 1: 
            print("setting angle to {}" .format(angle))
        self.pub_rudder.publish(angle)
        self.angle = angle
class Propeller:
    def __init__(self,min_throttle, max_throttle):
        self.PROP_PUB_TOPIC = "motor_cmd/propeller"
        self.pub_prop = rospy.Publisher(self.PROP_PUB_TOPIC, Int8, queue_size=1)
        self.max_throttle = max_throttle
        self.min_throttle = min_throttle
        self.on = False
        self.throttle = min_throttle
        
    def set_throttle(self, throttle, comment=0):
        if throttle == 0:
            self.on = False
        else:
            self.on = True 
        if throttle > self.max_throttle:
            throttle = self.max_throttle
        elif throttle < self.min_throttle: 
            throttle = self.min_throttle
        if comment==1:
            print("setting throttle to {}" .format(throttle))
        self.pub_prop.publish(throttle)
        self.throttle = throttle
class Conveyor:
    def __init__(self):
        self.lowered = False
        self.on = False
        
    def turn_on(self, comment=0):
        if comment == 1:
            print("turning conveyor on")
        self.on = True
        
    def turn_off(self, comment=0):
        if comment == 1:
            print("turning conveyor off")
        self.on = False
        
    def lower(self, comment=0):
        if comment == 1:
            print("lowering conveyor")
        self.lowered = True
        
    def higher(self, comment=0):
        if comment == 1:
            print("rasing conveyor")
        self.lowered = False
#returns a list of the contours of the ball
class Vision:
    """
    An OpenCV pipeline generated by GRIP.
    """
    
    def __init__(self, camera_port, focal_length, object_width):
        """initializes all values to presets or None if need to be set
        """
        self.cam = cv2.VideoCapture(camera_port)
        self.focal_length = focal_length
        self.object_width = object_width 
        self.__hsl_threshold_hue = [0.0, 35.63139931740616]
        self.__hsl_threshold_saturation = [135.29676258992808, 255.0]
        self.__hsl_threshold_luminance = [89.43345323741006, 200.6058020477816]

        self.hsl_threshold_output = None

        self.__find_contours_input = self.hsl_threshold_output
        self.__find_contours_external_only = False

        self.find_contours_output = None

        self.__filter_contours_contours = self.find_contours_output
        self.__filter_contours_min_area = 50.0
        self.__filter_contours_min_perimeter = 0
        self.__filter_contours_min_width = 0
        self.__filter_contours_max_width = 1000
        self.__filter_contours_min_height = 0
        self.__filter_contours_max_height = 1000.0
        self.__filter_contours_solidity = [81.83453237410072, 100]
        self.__filter_contours_max_vertices = 1.0E11
        self.__filter_contours_min_vertices = 0
        self.__filter_contours_min_ratio = 0
        self.__filter_contours_max_ratio = 1000

        self.filter_contours_output = None


    def process(self, source0):
        """
        Runs the pipeline and sets all outputs to new values.
        """
        # Step HSL_Threshold0:
        self.__hsl_threshold_input = source0
        (self.hsl_threshold_output) = self.__hsl_threshold(self.__hsl_threshold_input, self.__hsl_threshold_hue, self.__hsl_threshold_saturation, self.__hsl_threshold_luminance)

        # Step Find_Contours0:
        self.__find_contours_input = self.hsl_threshold_output
        (self.find_contours_output) = self.__find_contours(self.__find_contours_input, self.__find_contours_external_only)

        # Step Filter_Contours0:
        self.__filter_contours_contours = self.find_contours_output
        self.contours = self.__filter_contours(self.__filter_contours_contours, self.__filter_contours_min_area, self.__filter_contours_min_perimeter, self.__filter_contours_min_width, self.__filter_contours_max_width, self.__filter_contours_min_height, self.__filter_contours_max_height, self.__filter_contours_solidity, self.__filter_contours_max_vertices, self.__filter_contours_min_vertices, self.__filter_contours_min_ratio, self.__filter_contours_max_ratio)
        
        # if there are no contours return can't find ball 
        if len(self.contours) == 0:
            return ("can't find ball")

        #find the bigest contour and set it to best contour
        mas_area = 0
        best_contour= 0
        for i in self.contours:
            area = cv2.contourArea(i)
        if area > mas_area:
            mas_area = area
            best_contour= i
        return best_contour   

    @staticmethod
    def __hsl_threshold(input, hue, sat, lum):
        """Segment an image based on hue, saturation, and luminance ranges.
        Args:
            input: A BGR numpy.ndarray.
            hue: A list of two numbers the are the min and max hue.
            sat: A list of two numbers the are the min and max saturation.
            lum: A list of two numbers the are the min and max luminance.
        Returns:
            A black and white numpy.ndarray.
        """
        out = cv2.cvtColor(input, cv2.COLOR_BGR2HLS)
        return cv2.inRange(out, (hue[0], lum[0], sat[0]),  (hue[1], lum[1], sat[1]))

    @staticmethod
    def __find_contours(input, external_only):
        """Sets the values of pixels in a binary image to their distance to the nearest black pixel.
        Args:
            input: A numpy.ndarray.
            external_only: A boolean. If true only external contours are found.
        Return:
            A list of numpy.ndarray where each one represents a contour.
        """
        if(external_only):
            mode = cv2.RETR_EXTERNAL
        else:
            mode = cv2.RETR_LIST
        method = cv2.CHAIN_APPROX_SIMPLE
        im2, contours, hierarchy =cv2.findContours(input, mode=mode, method=method)
        return contours
    

    @staticmethod
    def __filter_contours(input_contours, min_area, min_perimeter, min_width, max_width,
                        min_height, max_height, solidity, max_vertex_count, min_vertex_count,
                        min_ratio, max_ratio):
        """Filters out contours that do not meet certain criteria.
        Args:
            input_contours: Contours as a list of numpy.ndarray.
            min_area: The minimum area of a contour that will be kept.
            min_perimeter: The minimum perimeter of a contour that will be kept.
            min_width: Minimum width of a contour.
            max_width: MaxWidth maximum width.
            min_height: Minimum height.
            max_height: Maximimum height.
            solidity: The minimum and maximum solidity of a contour.
            min_vertex_count: Minimum vertex Count of the contours.
            max_vertex_count: Maximum vertex Count.
            min_ratio: Minimum ratio of width to height.
            max_ratio: Maximum ratio of width to height.
        Returns:
            Contours as a list of numpy.ndarray.
        """
        output = []
        for contour in input_contours:
            x,y,w,h = cv2.boundingRect(contour)
            if (w < min_width or w > max_width):
                continue
            if (h < min_height or h > max_height):
                continue
            area = cv2.contourArea(contour)
            if (area < min_area):
                continue
            if (cv2.arcLength(contour, True) < min_perimeter):
                continue
            hull = cv2.convexHull(contour)
            solid = 100 * area / cv2.contourArea(hull)
            if (solid < solidity[0] or solid > solidity[1]):
                continue
            if (len(contour) < min_vertex_count or len(contour) > max_vertex_count):
                continue
            ratio = (float)(w) / h
            if (ratio < min_ratio or ratio > max_ratio):
                continue
            output.append(contour)
        return output
        
    # returns a value between -1 and 1, negative means the object is to the right of the viewer, positive means left
    def is_left(self,img):
	if img is None: 
	    return("Can't find camera")
        HEIGHT, WIDTH, channel = img.shape
        contours = self.process(img)
        if str(contours) == "can't find ball":
            return "can't find ball"
        middle = WIDTH / 2
        #find the average of the bigest x value and the smallest x value of contours
        lst = []
        for i in contours:
            lst.append(i[0][0] - middle)
        max_lst = max(lst)
        min_lst = min(lst)
        average = (max_lst + min_lst) / 2
        return -(float(average) / float(middle))
	
    
    #returns the distance between an object and the camera        
    def find_distance(self,img):
        contours = self.process(img)
        if len(contours) == 0:
            return 0 
        (x,y), radius = cv2.minEnclosingCircle(contours)
        px_width = radius * 2
        return (self.object_width * self.focal_length) / px_width
	
        
    def find_object_position(self):
        #ret,frame = self.cam.read()
	frame = cv2.imread("ping.jpg")
	#print(frame)
        is_left = self.is_left(frame)
        if is_left == "can't find ball": 
            return None, None 
	elif is_left == "Can't find camera": 
	    return "camera", None
        distance = self.find_distance(frame)
        return is_left, distance

class Boat:
    #conveyor_distance: distance to lower the conveyor
    #conveyor_on: distance to turn the conveyor on
    def __init__(self, conveyor_lower, conveyor_on, comment=0):
        self.RUDDER_MIN_ANGLE = -40
        self.RUDDER_MAX_ANGLE = 40
        self.PROPELLER_MIN_THROTTLE = -128
        self.PROPELLER_MAX_THROTTLE = 127
        self.VISION_FOCAL_LENGTH = 35 #mm
        self.VISION_OBJECT_WIDTH = 40 #mm
        self.CAMERA_PORT = 2
        self.conveyor_lower = conveyor_lower
        self.conveyor_on = conveyor_on
        self.comment = comment
        self.rudder = Rudder(self.RUDDER_MIN_ANGLE, self.RUDDER_MAX_ANGLE)
        self.propeller = Propeller(self.PROPELLER_MIN_THROTTLE, self.PROPELLER_MAX_THROTTLE)
        self.conveyor = Conveyor()
        self.vision = Vision(self.CAMERA_PORT, self.VISION_FOCAL_LENGTH, self.VISION_OBJECT_WIDTH)

    # turns the motor based on the value is_left returns
    #TODO add in comment parameters
    def drive(self, comment=None):
        #default
        if comment is None:
            comment = self.comment
            
        #constants
        #the absolute value of the angle must be more than this in order for the rudder to be set to anything other than 0
        SIGNIFICANT_RUDDER_ANGLE = 0.1
        #proportion of the max propeller speed that the propeller should run at based on what the conveyor belt should be doing
        SPEEDS = {"on":.25, "lowered":.5, "unlowered":1}
            
        left_val, distance = self.vision.find_object_position()
        if left_val is None: 
            print("can't find ball")
	elif left_val == "camera": 
	    print("can't find camera")
        else:
            angle = value_from_prop(left_val, self.RUDDER_MIN_ANGLE, self.RUDDER_MAX_ANGLE)
            
            #stop it from correcting super slight angles
            if abs(angle) < SIGNIFICANT_RUDDER_ANGLE:
                angle = 0
            #move the rudder
            self.rudder.set_angle(angle, self.comment)
        
            if self.conveyor_lower < distance:
                self.propeller.set_throttle(self.propeller.max_throttle*SPEEDS["unlowered"], self.comment)
                
            elif self.conveyor_on < distance and distance < self.conveyor_lower:
                self.propeller.set_throttle(self.propeller.max_throttle*SPEEDS["lowered"], self.comment)
                if self.conveyor.lowered == False: 
                    self.conveyor.lower()
                    
            elif distance < self.conveyor_on:
                self.propeller.set_throttle(self.propeller.max_throttle*SPEEDS["on"],self.comment)
                if self.conveyor.on == False:
                    self.conveyor.turn_on()
                if self.conveyor.lowered == False: 
                    self.conveyor.lower()
                    
            else: #turn coneyor off 
                self.propeller.set_throttle(self.propeller.min_throttle, self.comment)
                if self.conveyor.on == True: 
                    self.conveyor.turn_off()
                if self.conveyor.lowered == True: 
                    #raise the conveyor belt
                    self.conveyor.higher() 
            
            command = None   
            if not(command is None):
                print("running the following command {}".format(command))
                    


boat = Boat(40, 20, 1)
# start the ros node
rospy.init_node('main_2', anonymous=True)
rate = rospy.Rate(10) # 10hz
initial_flag = 1 
while not rospy.is_shutdown():

    boat.drive()
    rate.sleep()
