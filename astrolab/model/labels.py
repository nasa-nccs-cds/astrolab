from collections import OrderedDict
from typing import List, Union, Dict, Callable, Tuple, Optional, Any
import collections.abc
from functools import partial
from ..graph.flow import ActivationFlow
import traitlets.config as tlc
from astrolab.model.base import AstroSingleton, Marker
import xarray as xa
import numpy as np

def h2c( hexColor: str ) -> List[float]:
    hc = hexColor.strip( "# ")
    cv = [ int(hc[i0:i0+2],16) for i0 in range(0,len(hc),2) ]
    cv = cv if len(cv) == 4 else cv + [255]
    return [ c/255 for c in cv ]

def isIntRGB( color ):
    if isinstance(color, collections.abc.Sequence):
        for val in color:
            if val > 1: return True
    return False

def format_color( color: Union[str,List[Union[float,int]]] ) -> List[float]:
    if isinstance(color, str):  return h2c(color)
    elif isIntRGB(color):       return [c / 255 for c in color]
    else:                       return color

def format_colors( classes: List[Tuple[str,Union[str,List[Union[float,int]]]]] ) -> List[List[float]]:
    return [ format_color(color) for (label, color) in classes ]

def set_alphas( colors, alpha ):
    return [ set_alpha(color, alpha) for color in colors ]

def set_alpha( color, alpha ):
    return color[:3] + [alpha]

class Action:
    def __init__(self, type: str, source: str, pids: List[int], cid, **kwargs ):
        self.args = kwargs
        self.type = type
        self.cid=cid
        self.source = source
        self.pids = pids

    def __repr__(self):
        return f"A[{self.type}:{self.source} cid:{self.cid} pids:{self.pids}]"

    def __eq__(self, action: "Action" ):
        return ( self.type  == action.type ) and ( self.cid  == action.cid ) and ( self.source  == action.source ) and ( self.pids  == action.pids )

    @property
    def spec(self):
        return dict( atype=self.type, source=self.source , pids=self.pids, cid=self.cid, **self.args )



class LabelsManager(tlc.SingletonConfigurable,AstroSingleton):

    def __init__(self, **kwargs):
        super(LabelsManager, self).__init__(**kwargs)
        self._colors = None
        self._labels = None
        self.selectedClass = 0
        self._markers: List[Marker] = []
        self._flow: ActivationFlow = None
        self._actions = []
        self._labels_data: xa.DataArray = None
        self._optype = None
        self.template = None
        self.n_spread_iters = 1

    def flow(self) -> Optional[ActivationFlow]:
        return self._flow

    def addAction(self, type: str, source: str, pids: List[int], cid=None, **kwargs ):
        if cid == None: cid = self.selectedClass
        new_action = Action(type, source, pids, cid, **kwargs)
        print(f"ADD ACTION: {new_action}")
        if (len(self._actions) == 0) or (new_action != self._actions[-1]):
            self._actions.append( new_action )

    def popAction(self) -> Optional[Action]:
        try:
            action =  self._actions.pop()
            print( f"POP ACTION: {action}" )
            return action
        except:
            return None

    def undo(self):
        action = self.popAction()
        if action is not None:
            self.processAction( action )
            event = dict( event="gui", type="undo", **action.spec )
            self.submitEvent(event)

    def processAction(self, action: Action ):
        remaining_markers = []
        for marker in self._markers:
            marker.deletePids( action.pids )
            if not marker.isEmpty(): remaining_markers.append( marker )
        self._markers = remaining_markers

    @property
    def classification(self) -> np.ndarray:
        return self._flow.C

    def initLabelsData( self, point_data: xa.DataArray = None ):
        nodata_value = -1
        if point_data is not None:
            self.template = point_data[:,0].squeeze( drop=True )
            self.template.attrs = point_data.attrs
        if self.template is not None:
            self._labels_data: xa.DataArray = xa.full_like( self.template, 0, dtype=np.int32 ).where( self.template.notnull(), nodata_value )
            self._labels_data.attrs['_FillValue'] = nodata_value
            self._labels_data.name = self.template.attrs['dsid'] + "_labels"
            self._labels_data.attrs[ 'long_name' ] = [ "labels" ]

    def getMarker( self, pid: int ) -> Optional[Marker]:
        for marker in self._markers:
            if pid in marker.pids: return marker
        return None

    def updateLabels(self):
        for marker in self._markers:
            for pid in marker.pids:
                self._labels_data[ pid ] = marker.cid

    def labels_data( self ) -> xa.DataArray:
        self.updateLabels()
        return self._labels_data.copy( self._optype == "distance" )

    @classmethod
    def getSortedLabels(self, labels_dset: xa.Dataset ) -> Tuple[np.ndarray,np.ndarray]:
        labels: np.ndarray = labels_dset['C'].values
        distance: np.ndarray = labels_dset['D'].values
        indices = np.arange(labels.shape[0])
        indexed_labels = np.vstack( [ indices, labels ] ).transpose()
        selection = (labels > 0)
        filtered_labels = indexed_labels[selection]
        filtered_distance = distance[selection]
        return filtered_labels, filtered_distance

    def spread(self, optype: str,  n_iters = None ) -> Optional[xa.Dataset]:
        if self._flow is None:
            event = dict( event="message", type="warning", title='Workflow Message', caption="Awaiting task completion", msg="The data has not yet been loaded" )
            self.submitEvent( event )
            return None
        resume = ( optype == "neighbors" ) and ( self._optype == "neighbors" )
        if not resume: self._flow.clear()
        self._optype = optype
        labels_data = self.labels_data()
        niters = self.n_spread_iters if n_iters is None else n_iters
        return self._flow.spread( labels_data, niters )

    def clearTransient(self):
        if len(self._markers) > 0 and self._markers[-1].cid == 0:
            self._markers.pop(-1)

    def clearMarkers(self):
        self._markers = []
        self.initLabelsData()

    def addMarker(self, marker: Marker ):
        self.clearTransient()
        for pid in marker.pids: self.deletePid( pid )
        self._markers = list(filter( lambda m: not m.isEmpty(),  self._markers ))
        self._markers.append(marker)

    def popMarker(self) -> Marker:
        marker = self._markers.pop( -1 ) if len( self._markers ) else None
        event = dict( event="gui", type="undo", marker=marker )
        self.submitEvent( event )
        return marker

    def deletePid(self, pid: int ) -> List[Marker]:
        markers = []
        for marker in self._markers:
            if marker.deletePid( pid ): markers.append( marker )
        return markers

    @property
    def currentMarker(self) -> Marker:
        marker = self._markers[ -1 ] if len( self._markers ) else None
        return marker

    def getMarkers( self ) -> List[Marker]:
        return self._markers

    @property
    def selectedLabel(self):
        return self._labels[ self.selectedClass ]

    def selectedColor(self, mark: bool ) -> Tuple[int,List[float]]:
        icolor = self.selectedClass if mark else 0
        return icolor, self._colors[ icolor ]

    @property
    def colors(self)-> List[Tuple]:
        return self._colors

    @property
    def labels(self) -> List[str]:
        return self._labels

    @property
    def nLabels(self) -> int:
        return len(self._labels)

    def setLabels(self, labels: List[Tuple[str, List[float]]], **kwargs):
        unlabeled_color = kwargs.get( 'unlabeled', [1.0, 1.0, 0.0, 1.0] )
        label_list = [ ('Unlabeled', unlabeled_color ) ] + labels
        self._colors = format_colors( label_list )
        self._labels = [ item[0] for item in label_list ]

    def toDict( self, alpha ) -> OrderedDict:
        labels_dict = OrderedDict()
        for index, label in enumerate(self._labels):
            labels_dict[ label ] = set_alpha( self._colors[index], alpha )
        return labels_dict

    # def gui(self, **kwargs ):
    #     from hyperclass.learn.manager import learningManager
    #     self.show_unlabeled = kwargs.get( 'show_unlabeled', True )
    #     with_learning = kwargs.get( 'learning', False )
    #     self.console = QWidget()
    #     console_layout = QVBoxLayout()
    #     self.console.setLayout( console_layout )
    #     radio_button_style = [ "border-style: outset", "border-width: 4px", "padding: 6px", "border-radius: 10px" ]
    #
    #     labels_frame = QFrame( self.console )
    #     buttons_frame_layout = QVBoxLayout()
    #     labels_frame.setLayout( buttons_frame_layout )
    #     labels_frame.setFrameStyle( QFrame.StyledPanel | QFrame.Raised )
    #     labels_frame.setLineWidth( 3 )
    #     console_layout.addWidget( labels_frame )
    #     title = QLabel( "Classes" )
    #     title.setStyleSheet("font-weight: bold; color: black; font: 16pt" )
    #     buttons_frame_layout.addWidget( title )
    #
    #     for index, label in enumerate(self._labels):
    #         if (index > 0) or self.show_unlabeled:
    #             radiobutton = QRadioButton( label, self.console )
    #             radiobutton.index = index
    #             raw_color = [str(int(c * 155.99)) for c in self._colors[index]]
    #             qcolor = [ str(150+int(c*105.99)) for c in self._colors[index] ]
    #             style_sheet = ";".join( radio_button_style + [ f"background-color:rgb({','.join(qcolor)})", f"border-color: rgb({','.join(raw_color)})" ] )
    #             radiobutton.setStyleSheet( style_sheet )
    #             radiobutton.toggled.connect(self.onClicked)
    #             buttons_frame_layout.addWidget( radiobutton )
    #             self.buttons.append( radiobutton )
    #
    #     buttons_frame = QFrame( self.console )
    #     buttons_frame_layout = QVBoxLayout()
    #     buttons_frame.setLayout( buttons_frame_layout )
    #     buttons_frame.setFrameStyle( QFrame.StyledPanel | QFrame.Raised )
    #     buttons_frame.setLineWidth( 3 )
    #     console_layout.addWidget( buttons_frame )
    #     title = QLabel( "Actions" )
    #     title.setStyleSheet("font-weight: bold; color: black; font: 16pt" )
    #     buttons_frame_layout.addWidget( title )
    #     actions = [ 'Mark', 'Spread', 'Distance', 'Embed' ]
    #     if with_learning:
    #         actions = actions + [ 'Learn', 'Apply' ]
    #         learningManager.activate()
    #     actions = actions + [ 'Undo', 'Clear' ]
    #
    #     for action in actions:
    #         pybutton = QPushButton( action, self.console )
    #         pybutton.clicked.connect( partial( self.execute,action)  )
    #         buttons_frame_layout.addWidget(pybutton)
    #
    #     console_layout.addStretch( 1 )
    #     self.buttons[0].setChecked( True )
    #     self.activate_event_listening()
    #     return self.console

    def execute(self, action: str ):
        print( f"Executing action {action}" )
        etype = action.lower()
        if etype == "undo":
            self.undo()
        elif etype == "clear":
            event = dict( event='gui', type='clear', label='reinit dataset', markers="keep"  )
            self.submitEvent( event)
        elif etype == "spread":
            new_classes: Optional[xa.DataArray] = self.spread( etype )
            if new_classes is not None:
                event = dict( event="gui", type="spread", labels=new_classes )
                self.submitEvent(event)
        elif etype == "distance":
            new_classes: Optional[xa.DataArray] = self.spread( etype, 100 )
            if new_classes is not None:
                event = dict(event="gui", type="distance", labels=new_classes)
                self.submitEvent(event)
        elif etype == "embed":
            event = dict( event="gui", type="embed", alpha = 0.25 )
            self.submitEvent( event )
        elif etype == "mark":
            event = dict( event='gui', type=etype )
            self.submitEvent( event )
        elif etype in [ "apply", "learn" ]:
            event = dict( event='classify', type= etype + ".prep" )
            self.submitEvent( event )

    def onClicked(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            self.selectedClass = radioButton.index
            print(f"Selected class {radioButton.index}")

    def setClassIndex(self, cid: int ):
        self.selectedClass = cid
        for button in self.buttons:
            button.setChecked( cid == button.index )
        self.console.update()
