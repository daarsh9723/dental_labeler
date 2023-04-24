
# importing the tkinter module and PIL
# that is pillow module
from cgitb import text
import copy
from dataclasses import dataclass
import dataclasses
from genericpath import exists
import glob
import json
import math
import numpy as np
from textwrap import fill, indent
from tkinter import *
from PIL import ImageTk, Image


class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            return super().default(o)

#verify if qudrant is needed        
positions_by_quadrants = {
    "Quadrant 1":[],
    "Quadrant 2":[],
    "Quadrant 3":[],
    "Quadrant 4":[]
    
}


def reset_state_full():
    global state
    global canvas
    global label_active_class
    state = copy.deepcopy(state_default)
    # delete all the lines
    canvas.delete('line')
    canvas.delete('circle')

    for state_class in state['classes'][1:]:
        canvas.delete(state_class['name'])
    if label_active_class is not None:
        label_active_class.destroy()

def reset_state_part():
    global state
    global canvas
    global active_lines
    global active_circle_coordinates
    global bezier_curve
    global distance_text

    canvas.delete('line')
    canvas.delete('circle')
    canvas.delete('curve')
    canvas.delete('text')

    active_lines.clear()
    active_circle_coordinates.clear()
    bezier_curve.reinitialize()
    distance_text.delete('1.0', END)


def delete_selection():
    #to-do
    #if an entity is deleted, the dependent entities should also be deleted
    #Ex: delete a point, delete the line associated to the point (the second point can remain)
    return

def create_circle(canvasName,x, y, r=1.5,tag = 'circle',color = 'blue'): #center coordinates, radius
    x0 = x - r
    y0 = y - r
    x1 = x + r
    y1 = y + r
    return canvasName.create_oval(x0, y0, x1, y1,tag = tag,fill = color)

def create_line_across_canvas(canvas,x_1, y_1, x_2, y_2,color='yellow',width=0.5):
    global canvas_width
    # use equation of a line to extend the line to the end of the canvas, while maintaining the same slope

    m = (y_2 - y_1) / (x_2 - x_1) if (x_2 - x_1) != 0 else 1e10
    b = y_1 - m * x_1
    x_end = MAX_SIZE
    y_end = m * x_end + b
    x_start = 0
    y_start = m * x_start + b
    canvas.create_line(x_start, y_start, x_end, y_end,width=width,fill=color,tag='line')

def create_line(canvas, x1, y1, x2, y2, color = "yellow", width = 0.5):
    return canvas.create_line(x1, y1, x2, y2, width=width, fill=color, tag="line")


@dataclass
class Point:
    x: int
    y: int
    __point__:bool = True

def on_button_3_clicked(tk_event):
    global canvas
    global state
    global active_circle_coordinates
    global active_lines

    if len(active_circle_coordinates) == 0:
        (create_circle(canvas, tk_event.x, tk_event.y))
        active_circle_coordinates.append(Point(tk_event.x, tk_event.y))

    else:
        create_circle(canvas, tk_event.x, tk_event.y)
        line = canvas.create_line(active_circle_coordinates[0].x, active_circle_coordinates[0].y, tk_event.x, tk_event.y, tag='line', fill='red')
        active_circle_coordinates.clear()
        active_lines.append(line)


def get_line_equation(x1, y1, x2, y2):
    a = y2 - y1
    b = x1 - x2
    c = x2 * y1 - x1 * y2
    return a, b, c


def leftKey(event):
    global left_key_func
    if left_key_func != None:
        left_key_func(event)


def rightKey(event):
    global right_key_func
    if right_key_func != None:
        right_key_func(event)


class BezierCurve:
    def __init__(self, canvas):
        self.canvas = canvas
        self.points = []
        self.curve = None
        self.active_point = None

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def reinitialize(self):
        self.points = []
        self.curve = None
        self.active_point = None

    def on_click(self, event):
        x, y = event.x, event.y
        self.points.append((x, y))
        self.active_point = len(self.points) - 1
        self.draw_curve()

    def on_release(self, event):
        self.active_point = None

    def draw_curve(self):
        if self.curve is not None:
            self.canvas.delete(self.curve)

        if len(self.points) >= 2:
            curve_points = []
            n = len(self.points) - 1
            for t in np.linspace(0, 1, 100):
                x, y = 0, 0
                for i, (px, py) in enumerate(self.points):
                    b = self.binomial(n, i)
                    x += b * t**i * (1-t)**(n-i) * px
                    y += b * t**i * (1-t)**(n-i) * py
                curve_points.append(x)
                curve_points.append(y)

            self.curve = self.canvas.create_line(curve_points, fill="red", smooth=True, tag='curve')

        for i, (x, y) in enumerate(self.points):
            create_circle(self.canvas, x, y)
            self.canvas.create_text(x+10, y-10, text=f"P{i}", tag='text')

    def binomial(self, n, k):
        return np.math.factorial(n) // (np.math.factorial(k) * np.math.factorial(n-k))
    
    def point(self, t):
        p = self.points[:]
        while len(p) > 1:
            p = [tuple(p[i][j] + t * (p[i+1][j] - p[i][j]) for j in range(2)) for i in range(len(p)-1)]
        return p[0]

    def length(self, n=100):
        length = 0
        prev_point = self.point(0)
        for i in range(1, n+1):
            t = i / n
            point = self.point(t)
            segment_length = math.sqrt((point[0]-prev_point[0])**2 + (point[1]-prev_point[1])**2)
            length += segment_length
            prev_point = point
        return length


def create_canvas(image):
    global root
    canvas = Canvas(root, width=MAX_SIZE, height =MAX_SIZE )

    # We have to show the the box so this below line is needed

    canvas.create_image(10, 10, anchor=NW, image=image)
    canvas.grid(row=1, column=0, columnspan=4)
    canvas.bind("<Button-3>", on_button_3_clicked)
    
    return canvas

def save_state(image_path,current_path):
    global state
    # open json file and save current state in it
    with open('db.json', 'r') as f:
        db = json.load(f)
        db['data'][image_path] = state
        db['current_image'] = current_path
    with open('db.json', 'w') as f:
        json.dump(db, f,cls=EnhancedJSONEncoder,indent=4)

def decode_point(dct):
    if "__point__" in dct:
        return Point(dct["x"], dct["y"])
    else:
        return dct

def draw_line(e):
   x, y = e.x, e.y
   if canvas.old_coords:
      x1, y1 = canvas.old_coords
      canvas.create_line(x, y, x1, y1, width=5)
   canvas.old_coords = x, y


def load_state(image_path):
    global state
    global canvas
    reset_state_full()
    # open json file and load state from it
    with open('db.json', 'r') as f:
        db = json.load(f,object_hook=decode_point)

        if image_path in db['data']:
            state = db['data'][image_path]
            state = update_state_with_new_classes(state) 
            for state_class in state['classes']:
                if state_class['name'] == 'Gonion':
                    if state_class['first_line'] !=False:
                        line = state_class['first_line']
                        redraw_line(line)
                    if state_class['second_line'] !=False:
                        line = state_class['second_line']
                        redraw_line(line)
                        if len(line) == 2:
                            create_angle_bisector(canvas)
                    if state_class['third_mouse_click'] !=False:
                        x,y,c =  state_class['bisector']
                        x_pos,y_pos = get_circle_loc_on_bisector(state_class['third_mouse_click'], x, y, c)
                        create_circle(canvas,x_pos,y_pos,r=2,tag='bisector_circle',color='yellow')
                        state_class['bisector_draw'] = False
                else:
                    if state_class['pos']!=False:
                        create_circle(canvas,state_class['pos'].x,state_class['pos'].y,tag=state_class['name'],color=state_class['color'])
                        

def forward(img_path):
    global canvas
    global button_forward
    global button_back
    global button_clear
    global button_measure_line
    global state
    global img_paths
    global current_image
    global current_image_path

    canvas.grid_forget()

    # save_state(current_image_path,img_path)
    current_image_path = img_path

    current_image = create_image_from_path(img_path)
    current_image_path = img_path
    canvas = create_canvas(current_image)

    # load_state(current_image_path)
    create_forward_button(img_path)
    create_back_button(img_path)

    button_measure_line.grid(row=5, column=0)
    button_clear.grid(row=5, column=1)
    button_forward.grid(row=5, column=2)
    button_back.grid(row=5, column=3)


def create_forward_button(img_path):
    global button_forward
    global right_key_func
    if img_paths.index(img_path) == len(img_paths)-1:
        button_forward = Button(root, text="Forward",
                                state=DISABLED)
        right_key_func = lambda event: None
    else:
        button_forward = Button(root, text="forward",
                        command=lambda: forward(img_paths[img_paths.index(img_path)+1]))
        right_key_func = lambda event: forward(img_paths[img_paths.index(img_path)+1])

    
def back(img_path):

    global canvas
    global button_forward
    global button_back
    global button_clear
    global state
    global img_paths
    global current_image
    global current_image_path

    canvas.grid_forget()
    # save_state(current_image_path,img_path)
    current_image_path = img_path
    # for clearing the image for new image to pop up
    current_image = create_image_from_path(img_path)
    current_image_path = img_path
    canvas = create_canvas(current_image)
    create_forward_button(img_path)
    create_back_button(img_path)


    button_back.grid(row=5, column=3)
    button_clear.grid(row=5, column=1)
    button_forward.grid(row=5, column=2)
    # label_active_class.grid(row=5, column=3)

def create_back_button(img_path):
    global button_back
    global left_key_func

    if img_paths.index(img_path) == 0:
        button_back = Button(root, text="Back", state=DISABLED)
        left_key_func = lambda event: None
    else:
        button_back = Button(root, text="Back",command=lambda: back(img_paths[img_paths.index(img_path)-1]))
        left_key_func = lambda event: back(img_paths[img_paths.index(img_path)-1])


def show_distance(distance, type_of_line):
    global canvas 
    global root
    global distance_text

    distance_text = Text(canvas, width=25, height=5)
    canvas.create_window((715, 800), window=distance_text)

    distance_text.insert(END, f"Length of {type_of_line}:{distance:.2f}")

    return


def measure_distance(x1, y1, x2, y2):
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def measure():
    global active_lines
    distance = 0
    for line in active_lines:
        x1, y1, x2, y2 = canvas.coords(line)
        distance += measure_distance(x1, y1, x2, y2)
    show_distance(distance, "line")
    return  

def measure_curve():
    global bezier_curve
    distance = 0
    distance = bezier_curve.length()
    show_distance(distance, 'curve')


def main():
    global root
    root = Tk()
    root.title("Dental Image Labeller")
    root.geometry("1000x1000")

    global frame

    #define the global vars
    global img_paths
    global canvas
    global button_forward
    global button_back
    global button_clear
    global button_measure_line
    global button_measure_curve
    global current_image
    global current_image_path
    global left_key_func
    global right_key_func
    global active_circle_coordinates
    global active_lines
    global active_curves
    global bezier_curve

    active_circle_coordinates = []
    active_lines = []
    active_curves = []

    img_paths = glob.glob("images/*.jpg")
    img_paths.extend(glob.glob("images/*.JPG")) #looks like just a duplicated list

    if exists('db.json'):
        with open('db.json', 'r') as f:
            db = json.load(f)
    else:
        db = {
            "current_image":img_paths[0],
            "data":{}
        }
        json.dump(db, open('db.json', 'w'),indent=4)

    current_image_path = db['current_image'] if db['current_image'] in img_paths else img_paths[0]
    current_image = create_image_from_path(current_image_path)
    canvas = create_canvas(current_image)
    bezier_curve = BezierCurve(canvas)

    # load_state(current_image_path)

   
    create_forward_button(current_image_path)
    create_back_button(current_image_path)

    button_measure_line = Button(root, text="Measure Line", command=measure)
    button_measure_curve = Button(root, text="Measure Curve", command=measure_curve)
    button_clear = Button(root, text="Clear", command=reset_state_part)

    button_measure_line.grid(row=5, column=0)
    button_clear.grid(row=5, column=1)
    button_forward.grid(row=5, column=2)
    button_back.grid(row=5, column=3)
    button_measure_curve.grid(row=5, column=4)

    root.mainloop()

# def make_state_default():
#     state_default = {
#         'classes':[
#         {
            
#         }
#         ]
#     }
#     return

def make_table():
    global state
    global root
    global canvas

    state_char_map = {
        True:'X',
        False:'V'
    }
    data = [[f"{i['name']} ({inv_class_name_shortcut[i['name']]})",state_char_map[i['pos']==False]] for i in state['classes'] if i['name'] != 'Gonion' ]

    t = Table(root,data)

    t.frame1.grid(row=1, column=6)
    #change_class_func(None,state["active_class"])
    #root.update()
    #canvas.focus_set()
    create_circle(canvas,0,0)


def create_image_from_path(image):
    pil_im = Image.open(image)
    pil_im = pil_im.resize((MAX_SIZE, MAX_SIZE), Image.ANTIALIAS)
    im =ImageTk.PhotoImage(pil_im)
    return im

MAX_SIZE = 800


def redraw_line(line):
    for line_event in line:
        create_circle(canvas,line_event.x,line_event.y)
    if len(line) == 2:
        create_line_across_canvas(canvas, line[0].x, line[0].y, line[1].x, line[1].y)

class Table:
     
    def __init__(self,root,lst):
        self.frame1 = Frame(root, background="black")

        # code for creating table
        for i in range(len(lst)):
            for j in range(len(lst[0])):
                 
                self.e = Entry(self.frame1, width=15 if j==0 else 3, fg='black',
                               font=('Arial',16))
                 
                self.e.grid(row=i, column=j)
                self.e.insert(END, lst[i][j])

  
main()
