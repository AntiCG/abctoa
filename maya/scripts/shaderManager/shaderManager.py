# Alembic Holder
# Copyright (c) 2014, Gael Honorez, All rights reserved.
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library.


import os
import shiboken


d = os.path.dirname(__file__)

import json
from arnold import *

from PySide import QtGui, QtCore
from PySide.QtGui import *
from PySide.QtCore import *

from gpucache import gpucache, treeitem, treeDelegate, treeitemWildcard
reload(treeitem)
reload(treeitemWildcard)
reload(treeDelegate)
reload(gpucache)
from propertywidgets.property_editorByType import PropertyEditor

from ui import UI_ABCHierarchy
reload(UI_ABCHierarchy)


import maya.cmds as cmds
import maya.mel as mel

from maya.OpenMaya import MObjectHandle, MDGMessage, MMessage, MNodeMessage, MFnDependencyNode, MObject
import maya.OpenMayaUI as apiUI


def getMayaWindow():
    """
    Get the main Maya window as a QtGui.QMainWindow instance
    @return: QtGui.QMainWindow instance of the top level Maya windows
    """
    ptr = apiUI.MQtUtil.mainWindow()
    if ptr is not None:
        return shiboken.wrapInstance(long(ptr), QtGui.QMainWindow)


class List(QMainWindow, UI_ABCHierarchy.Ui_NAM):
    def __init__(self, parent=None):
        super(List, self).__init__(parent)
        
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)        
        
        if not AiUniverseIsActive():
            AiBegin()

        self.setupUi(self)



        self.shadersFromFile = []
        self.displaceFromFile = []

        self.curLayer = None
        # self.listTagsWidget = tagTree(self)
        # self.tagGroup.layout().addWidget(self.listTagsWidget)
        #self.tagGroup.setVisible(0)

        self.shaderToAssign = None
        self.ABCViewerNode = {}
        self.tags = {}
        self.getNode()
        self.getCache()
        self.thisTagItem = None
        self.thisTreeItem = None

        self.lastClick = -1

        self.propertyEditing = False

        self.propertyEditorWindow = QtGui.QDockWidget(self)
        self.propertyEditorWindow.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.propertyEditorWindow.setWindowTitle("Properties")
        self.propertyEditorWindow.setMinimumWidth(300)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.propertyEditorWindow)
        self.propertyEditor = PropertyEditor(self, "polymesh", self.propertyEditorWindow)
        self.propertyEditorWindow.setWidget(self.propertyEditor)


        self.propertyEditor.propertyChanged.connect(self.propertyChanged)

        self.hierarchyWidget.setColumnWidth(0,600)
        self.hierarchyWidget.setIconSize(QSize(22,22))

        self.hierarchyWidget.dragEnterEvent = self.newhierarchyWidgetdragEnterEvent
        self.hierarchyWidget.dragMoveEvent = self.newhierarchyWidgetdragMoveEvent
        self.hierarchyWidget.dropEvent = self.newhierarchyWidgetDropEvent

        self.hierarchyWidget.setColumnWidth(0,200)
        self.hierarchyWidget.setColumnWidth(1,300)
        self.hierarchyWidget.setColumnWidth(2,300)

        self.hierarchyWidget.setItemDelegate(treeDelegate.treeDelegate(self))

        self.populate()

        self.curPath = ""
        self.ABCcurPath = ""

        self.hierarchyWidget.itemDoubleClicked.connect(self.itemDoubleClicked)
        self.hierarchyWidget.itemExpanded.connect(self.requireItemExpanded)
        self.hierarchyWidget.itemCollapsed.connect(self.requireItemCollapse)
        self.hierarchyWidget.itemClicked.connect(self.itemCLicked)
        self.hierarchyWidget.itemPressed.connect(self.itemPressed)



        

        #self.shadersList.startDrag = self.newshadersListStartDrag
        self.shadersList.itemPressed.connect(self.shaderCLicked)
        self.shadersList.mouseMoveEvent = self.newshadersListmouseMoveEvent


        self.displacementList.itemPressed.connect(self.shaderCLicked)
        self.displacementList.mouseMoveEvent = self.newdisplaceListmouseMoveEvent

        self.refreshShadersBtn.pressed.connect(self.refreshShaders)

        self.refreshShaders()

        if AiUniverseIsActive() and AiRendering() == False:
             AiEnd()


        self.getLayers()
        self.renderLayer.currentIndexChanged.connect(self.layerChanged)
        self.NodeNameMsgId  = MNodeMessage.addNameChangedCallback( MObject(), self.nameChangedCB )
        self.newNodeCBMsgId = MDGMessage.addNodeAddedCallback( self.newNodeCB )
        self.delNodeCBMsgId = MDGMessage.addNodeRemovedCallback( self.delNodeCB )

        self.disableLayerOverrides()

        self.overrideDisps.stateChanged.connect(self.overrideDispsChanged)
        self.overrideShaders.stateChanged.connect(self.overrideShadersChanged)
        self.overrideProps.stateChanged.connect(self.overridePropsChanged)


        #Widcard management
        self.wildCardButton.pressed.connect(self.addWildCard)

        self.setCurrentLayer()
        self.layerChangedJob = cmds.scriptJob( e= ["renderLayerManagerChange",self.setCurrentLayer])

    def overrideDispsChanged(self, state):
        result = True
        if state == 0:
            result = False


        if self.getLayer() == None:
            return

        for shape in self.ABCViewerNode:
            assignations = self.ABCViewerNode[shape].getAssignations()
            assignations.setRemovedDisplace(self.getLayer(), result)

        self.updateTree()

    def overrideShadersChanged(self, state):

        result = True
        if state == 0:
            result = False

        if self.getLayer() == None:
            return

        for shape in self.ABCViewerNode:
            assignations = self.ABCViewerNode[shape].getAssignations()
            assignations.setRemovedShader(self.getLayer(), result)

        self.updateTree()


    def overridePropsChanged(self, state):
        result = True
        if state == 0:
            result = False

        if self.getLayer() == None:
            return

        for shape in self.ABCViewerNode:
            assignations = self.ABCViewerNode[shape].getAssignations()
            assignations.setRemovedProperties(self.getLayer(), result)

        self.updateTree()

    def createSG(self, node):
        sg = None

        SGs = cmds.listConnections( node, d=True, s=False, type="shadingEngine")        
        if not SGs:
            try:
                sg = cmds.shadingNode("shadingEngine", n="%sSG" % node, asRendering=True)
                cmds.connectAttr("%s.outColor" % node, "%s.surfaceShader" % sg, force=True)
                return sg
            except:
                print "Error creating shading group for node", node
        else:
            return SGs[0]
        


    def nameChangedCB(self, node, prevName, client):
        ''' Callback when a node is renamed '''

        if prevName == "" or not prevName or prevName.startswith("_"):
            return
        handle = MObjectHandle( node )
        if not handle.isValid():
            return
        mobject = handle.object()

        nodeFn = MFnDependencyNode ( mobject )
        nodeName = nodeFn.name()
        
        if cmds.getClassification(cmds.nodeType(nodeName), satisfies="shader"):

            if cmds.nodeType(nodeName) == "displacementShader":
                items = self.displacementList.findItems(prevName, QtCore.Qt.MatchExactly)
                for item in items:
                    item.setText(nodeName)

                # renaming shaders in caches
                for cache in self.ABCViewerNode.values():
                    cache.renameDisplacement(prevName, nodeName)
                self.checkShaders()
            else:
                items = self.shadersList.findItems(prevName, QtCore.Qt.MatchExactly)
                for item in items:
                    item.setText(nodeName)

        if cmds.nodeType(nodeName) == "shadingEngine":
                # renaming shaders in caches
                for cache in self.ABCViewerNode.values():
                    cache.renameShader(prevName, nodeName)

                self.checkShaders()


    def newNodeCB(self, newNode, data ):
        ''' Callback when creating a new node '''
        mobject = MObjectHandle( newNode ).object()
        nodeFn = MFnDependencyNode ( mobject )
        nodeName = nodeFn.name()
        if cmds.getClassification(cmds.nodeType(nodeName), satisfies="shader"):
            if cmds.nodeType(nodeName) == "displacementShader":
                icon = QtGui.QIcon()
                icon.addFile(os.path.join(d, "../../icons/sg.xpm"), QtCore.QSize(25,25))
                item = QtGui.QListWidgetItem(nodeName)
                item.setIcon(icon)
                self.displacementList.addItem(item)
            else:

                icon = QtGui.QIcon()
                icon.addFile(os.path.join(d, "../../icons/sg.xpm"), QtCore.QSize(25,25))
                item = QtGui.QListWidgetItem(nodeName)
                item.setIcon(icon)
                self.shadersList.addItem(item)


    def delNodeCB(self, node, data ):
        ''' Callback when a node has been deleted '''
        mobject = MObjectHandle( node ).object()
        nodeFn = MFnDependencyNode ( mobject )
        nodeName = nodeFn.name()

        didSomething = False

        if cmds.nodeType(nodeName) == "displacementShader":
            items = self.displacementList.findItems(nodeName, QtCore.Qt.MatchExactly)
            for item in items:
                self.displacementList.takeItem(self.displacementList.row(item))   

            # remove shaders from caches
            for cache in self.ABCViewerNode.values():
                didSomething = True
                cache.removeDisplacement(nodeName)

        else:
            items = self.shadersList.findItems(nodeName, QtCore.Qt.MatchExactly)
            for item in items:
                self.shadersList.takeItem(self.shadersList.row(item))

            # remove shaders from caches
            for cache in self.ABCViewerNode.values():
                didSomething = True
                cache.removeShader(nodeName)                
        
        if didSomething:
            self.checkShaders()

    def shaderCLicked(self, item):
        shader = item.text()
        if shader:
            if cmds.objExists(shader):
                try:
                    conn = cmds.connectionInfo(shader +".surfaceShader", sourceFromDestination=True)
                    if conn:
                        cmds.select(conn, r=1, ne=1)
                    else:
                        cmds.select(shader, r=1, ne=1)
                except:
                    cmds.select(shader, r=1, ne=1)

    def newshadersListmouseMoveEvent(self, event):
        self.newshadersListStartDrag(event)

    def newdisplaceListmouseMoveEvent(self, event):
        self.newdisplaceListStartDrag(event)

    def newshadersListStartDrag(self, event):
        index = self.shadersList.indexAt(event.pos())
        if not index.isValid():
            return
        selected = self.shadersList.itemFromIndex(index)

        self.shaderCLicked(selected)

        itemData = QtCore.QByteArray()
        dataStream = QtCore.QDataStream(itemData, QtCore.QIODevice.WriteOnly)
        dataStream << QtCore.QByteArray(str(selected.text()))

        mimeData = QtCore.QMimeData()
        mimeData.setData("application/x-shader", itemData)
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)

        drag.setPixmap(self.shadersList.itemAt(event.pos()).icon().pixmap(50,50))
        drag.setHotSpot(QtCore.QPoint(0,0))
        drag.start(QtCore.Qt.MoveAction)

    def newdisplaceListStartDrag(self, event):
        index = self.displacementList.indexAt(event.pos())
        if not index.isValid():
            return
        selected = self.displacementList.itemFromIndex(index)

        self.shaderCLicked(selected)

        itemData = QtCore.QByteArray()
        dataStream = QtCore.QDataStream(itemData, QtCore.QIODevice.WriteOnly)
        dataStream << QtCore.QByteArray(str(selected.text()))

        mimeData = QtCore.QMimeData()
        mimeData.setData("application/x-displacement", itemData)
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)

        drag.setPixmap(self.displacementList.itemAt(event.pos()).icon().pixmap(50,50))
        drag.setHotSpot(QtCore.QPoint(0,0))
        drag.start(QtCore.Qt.MoveAction)

    def newhierarchyWidgetdragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-shader") or event.mimeData().hasFormat("application/x-displacement"):
            event.accept()
        else:
            event.ignore()

    def newhierarchyWidgetdragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-shader") or event.mimeData().hasFormat("application/x-displacement"):
            event.accept()
        else:
            event.ignore()

    def newhierarchyWidgetDropEvent(self, event):
        mime = event.mimeData()
        itemData = None
        mode = 0
        
        if mime.hasFormat("application/x-shader"):
            mode = 0
            itemData = mime.data("application/x-shader")
        elif mime.hasFormat("application/x-displacement"):
            mode = 1
            itemData = mime.data("application/x-displacement")

        dataStream = QtCore.QDataStream(itemData, QtCore.QIODevice.ReadOnly)

        shader = QtCore.QByteArray()
        dataStream >> shader

        shader = str(shader)
        items = []
        
        selectedItems = self.hierarchyWidget.selectedItems()

        item = self.hierarchyWidget.itemFromIndex(self.hierarchyWidget.indexAt(event.pos()))
        if item:
            items.append(item)

        if len(selectedItems) > 1:
            items = items + selectedItems

        for item in items:
            item.shaderToAssign = shader
            if mode == 0:
                item.assignShader()
            elif mode == 1:
                item.assignDisplacement()
               
        event.accept()

    def closeEvent(self, event):
        print "removing scriptjob"
        cmds.scriptJob( kill=self.layerChangedJob, force=True)
        for cache in self.ABCViewerNode.values():
            cache.setSelection("")
        print "removing callbacks"
        MMessage.removeCallback( self.newNodeCBMsgId )
        MMessage.removeCallback( self.delNodeCBMsgId )
        MNodeMessage.removeCallback( self.NodeNameMsgId )
        return QtGui.QMainWindow.closeEvent(self, event)

    def setCurrentLayer(self):
        curLayer = cmds.editRenderLayerGlobals(query=1, currentRenderLayer=1)
        curLayeridx = self.renderLayer.findText(curLayer)
        if curLayeridx != -1:
            self.renderLayer.setCurrentIndex(curLayeridx)



    def layerChanged(self, index):


        self.curLayer = self.renderLayer.itemText(index)
        if self.curLayer == "defaultRenderLayer":
            self.disableLayerOverrides()
        else:
            self.enableLayerOverrides()
            for cache in self.ABCViewerNode:
                c = self.ABCViewerNode[cache]
                over = c.getLayerOverrides(self.getLayer())

                if over:
                    self.overrideProps.setChecked(over["removeProperties"])
                    self.overrideShaders.setChecked(over["removeShaders"])
                    self.overrideDisps.setChecked(over["removeDisplacements"])


        self.updateTree()
        if self.hierarchyWidget.currentItem():
            self.itemCLicked(self.hierarchyWidget.currentItem(), 0, force=True)

        # change it in maya too
        curLayer = cmds.editRenderLayerGlobals(query=1, currentRenderLayer=1)
        if curLayer != self.curLayer:
            cmds.editRenderLayerGlobals( currentRenderLayer=self.curLayer)



    def updateTree(self):
        items = []
        for i in range(self.hierarchyWidget.topLevelItemCount()):
            self.visitTree(items, self.hierarchyWidget.topLevelItem(i))

        for item in items:
            item.removeAssigns()
            item.checkShaders(self.getLayer())
            item.checkProperties(self.getLayer())


    def visitTree(self, items, treeitem):
        items.append(treeitem)
        for i in range(treeitem.childCount()):
            self.visitTree(items, treeitem.child(i))


    def enableLayerOverrides(self):
        self.overrideDisps.setEnabled(1)
        self.overrideShaders.setEnabled(1)
        self.overrideProps.setEnabled(1)


        self.overrideDisps.setChecked(0)
        self.overrideShaders.setChecked(0)
        self.overrideProps.setChecked(0)


    def disableLayerOverrides(self):
        self.overrideDisps.setEnabled(0)
        self.overrideShaders.setEnabled(0)
        self.overrideProps.setEnabled(0)

        self.overrideDisps.setChecked(0)
        self.overrideShaders.setChecked(0)
        self.overrideProps.setChecked(0)


    def getLayers(self):
        self.renderLayer.clear()
        renderLayers = []
        for layer in cmds.ls(type="renderLayer"):
            con = cmds.connectionInfo(layer + ".identification", sourceFromDestination=True)
            if con:
                if con.split(".")[0] == "renderLayerManager":
                    renderLayers.append(layer)

        self.renderLayer.addItems(renderLayers)
        idx = self.renderLayer.findText("defaultRenderLayer")
        if idx == -1:
            self.curLayer = self.renderLayer.itemText(0)
        else:
            self.curLayer = self.renderLayer.itemText(idx)
            self.renderLayer.setCurrentIndex(idx)

    def propertyChanged(self, prop):
        if self.propertyEditing:
            return
        try:
            self.propertyEditor.propertyChanged.disconnect()
        except:
            pass

        propName = prop["propname"]
        default = prop["default"]
        value = prop["value"]

        if self.lastClick == 1:

            item = self.hierarchyWidget.currentItem()
            curPath = item.getPath()
            if curPath is None:
                return

            cache = item.cache
            layer = self.getLayer()
            cache.updateOverride(propName, default, value, curPath, layer)
            self.updatePropertyColor(cache, layer, propName, curPath)

            self.checkProperties(self.getLayer(), item=item)

        elif self.lastClick == 2:
            item = self.listTagsWidget.currentItem()
            item.assignProperty(propName, default, value)


        self.propertyEditor.propertyChanged.connect(self.propertyChanged)


    def updatePropertyColor(self, cache, layer, propName, curPath):
        cacheState = cache.getPropertyState(layer, propName, curPath)
        if cacheState == 3:
            self.propertyEditor.propertyWidgets[propName].title.setText("<font color='darkRed'>%s</font>" % propName)
        if cacheState == 2:
            self.propertyEditor.propertyWidgets[propName].title.setText("<font color='red'>%s</font>" % propName)
        if cacheState == 1:
            self.propertyEditor.propertyWidgets[propName].title.setText("<font color='white'><i>%s</i></font>" % propName)


    def fillShaderList(self):
        self.shadersList.clear()
        shaders = cmds.ls(materials=True)
        icon = QtGui.QIcon()
        icon.addFile(os.path.join(d, "../../icons/sg.xpm"), QtCore.QSize(25,25))
        for shader in shaders:
            item = QtGui.QListWidgetItem(shader)
            item.setIcon(icon)
            self.shadersList.addItem(item)

    def fillDisplacementList(self):
        self.displacementList.clear()
        displaces = cmds.ls(type="displacementShader")
        icon = QtGui.QIcon()
        icon.addFile(os.path.join(d, "../../icons/displacement.xpm"), QtCore.QSize(25,25))
        for sg in displaces:
            item = QtGui.QListWidgetItem(sg)
            item.setIcon(icon)
            self.displacementList.addItem(item)

    def refreshShaders(self):
        self.fillShaderList()
        self.fillDisplacementList()

    def getLayer(self):
        if self.curLayer != "defaultRenderLayer":
            return self.curLayer
        return None

    def itemCLicked(self, item, col, force=False) :
        self.propertyEditing = True
        try:
            self.propertyEditor.propertyChanged.disconnect()
        except:
            pass

        self.lastClick = 1

        if self.thisTreeItem is item and force==False:
            self.propertyEditing = False
            return
        self.thisTreeItem = item

        state = item.checkState(col)
        curPath = item.getPath()
        cache = item.cache

        cache.setSelection(curPath)


        self.propertyEditor.resetToDefault()

        layer = self.getLayer()

        attributes = {}

        if layer:
            layerOverrides = cache.getAssignations().getLayerOverrides(layer)
            if not layerOverrides:
                layerOverrides = dict(removeDisplacements=False, removeProperties=False, removeShaders=False)

            if layerOverrides["removeProperties"] == False:
                attributes = cache.getAssignations().getOverrides(curPath, layer)
            else:
                attributes = cache.getAssignations().getOverrides(curPath, None)

        else:
            attributes = cache.getAssignations().getOverrides(curPath, None)


        if len(attributes) > 0 :
            for propname in attributes:
                value = attributes[propname].get("override") 
                self.propertyEditor.propertyValue(dict(paramname=propname, value=value))

                self.updatePropertyColor(cache, layer, propname, curPath)

        self.propertyEditor.propertyChanged.connect(self.propertyChanged)

        if state == 2 :
            cache.setToPath(curPath)

        elif state == 0:
            cache.setToPath("|")

        self.propertyEditing = False

    def itemPressed(self, item, col) :
        self.lastClick = 1
        if QtGui.QApplication.mouseButtons()  == QtCore.Qt.RightButton:
            item.pressed()


    def requireItemCollapse(self, item):
        pass

    def requireItemExpanded(self, item) :
        self.expandItem(item)

    def itemDoubleClicked(self, item, column) :
        if item.isWildCard:
            if not item.protected:
                text, ok = QtGui.QInputDialog.getText(self, 'WildCard expression',  'Enter the expression:', QtGui.QLineEdit.Normal, item.getPath())
                if ok:
                    #first change the path
                    item.setExpression(text)

        else:
            self.expandItem(item)

    def expandItem(self, item) :
        expandAll = False
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            expandAll = True

        if item.hasChidren():
            items = cmds.ABCHierarchy(item.cache.ABCcache, item.getPath().replace("/", "|"))
            if items != None :
                createdItems = self.createBranch(item, items)
                if expandAll :
                    for i in createdItems:
                        self.hierarchyWidget.expandItem(i)
                        self.expandItem(i)
            
            return


        item.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.DontShowIndicator)

    def createBranch(self, parentItem, abcchild, hierarchy = False, p = "/") :
        createdItems = []
        for item in abcchild :
            itemType = item.split(":")[0]
            itemName = item.split(":")[-1]

            itemExists = False
            for i in xrange(0, parentItem.childCount()) :
                text = parentItem.child(i).getDisplayPath()
                if str(text) == str(itemName) :
                    itemExists = True

            if itemExists == False :
                newItem = treeitem.abcTreeItem(parentItem.cache, parentItem.path + [itemName], itemType, self)
                parentItem.cache.itemsTree.append(newItem)

                newItem.checkShaders(self.getLayer())
                newItem.checkProperties(self.getLayer())
               
                # check if the item has chidren, but go no further...
                childsItems = cmds.ABCHierarchy(newItem.cache.ABCcache, newItem.getPath().replace("/", "|"))
                if childsItems:
                    newItem.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)
                    newItem.setHasChildren(True)
                else:
                    newItem.setHasChildren(False)

                parentItem.addChild(newItem)

                if hierarchy == True :
                    parentItem = newItem

                self.hierarchyWidget.resizeColumnToContents(0)
                createdItems.append(newItem)

        return createdItems

    def populate(self) :
        for cache in self.ABCViewerNode.values():
            if cache.cache != "":
                firstLevel = cmds.ABCHierarchy(cache.ABCcache)

                root = treeitem.abcTreeItem(cache, [], "Transform", self)
                #root.setCheckState(0, QtCore.Qt.Unchecked)
                root.checkShaders(self.getLayer())
                root.checkProperties(self.getLayer())
                root.setHasChildren(True)
                cache.itemsTree.append(root)

                if cache.ABCcurPath != None :
                    if cache.ABCcurPath != "/" :
                        paths = cache.ABCcurPath.split("/")
                        if len(paths) > 0 :
                            self.createBranch(root, paths[1:], True)

                self.hierarchyWidget.addTopLevelItem(root)
                self.createBranch(root,firstLevel)
                root.setExpanded(1)

            ### CHECK WILDCARD ASSIGNATIONS

            wildsAdded = []
            for wild in cache.assignations.getAllWidcards():
                name = wild["name"]
                if not name in wildsAdded:
                    wildsAdded.append(name)
                    self.createWildCard(root, name, wild["fromfile"])                


    def getShader(self):
        x = cmds.ls(mat=1, sl=1)
        if len(x) == 0:
            return None

        if cmds.nodeType(x[0]) == "displacementShader":
            return x[0]

        else:
            return self.createSG(x[0])


    def checkShaders(self, layer=None, item=None):

        if item is None or item.isWildCard == True:
            # we check every single item.
            for cache in self.ABCViewerNode.values():
                if cache.cache != "":
                    for item in cache.itemsTree:
                        item.checkShaders(layer)
        else:
            # we only check this item and his childrens
            item.checkShaders(layer)

            numChildren = item.childCount()
            for i in range(numChildren):
                self.checkShaders(layer, item.child(i))

    def checkProperties(self, layer=None, item=None):

        if item is None or item.isWildCard == True:
            # we check every single item.
            for cache in self.ABCViewerNode.values():
                if cache.cache != "":
                    for item in cache.itemsTree:
                        item.checkProperties(layer)
        else:
            # we only check this item and his childrens
            item.checkProperties(layer)
            numChildren = item.childCount()
            for i in range(numChildren):
                self.checkProperties(layer, item.child(i))
                    




    def getNode(self):
        tr = cmds.ls( type= 'transform', sl=1, l=1) + cmds.ls(type= 'alembicHolder', sl=1, l=1)
        if len(tr) == 0:
            return
        for x in tr:
            if cmds.nodeType(x) == "alembicHolder":
                shape = x
            else:
                shapes = cmds.listRelatives(x, shapes=True, f=1)
                if shapes:
                    shape = shapes[0]
            if cmds.nodeType(shape) == "gpuCache" or cmds.nodeType(shape) == "alembicHolder":

                self.ABCViewerNode[shape] = gpucache.gpucache(shape, self)
                cacheAssignations = self.ABCViewerNode[shape].getAssignations()

                if cmds.objExists(str(shape) + ".jsonFile"):
                    cur = cmds.getAttr("%s.jsonFile" % shape)
                    try:
                        f = open(cur, "r")
                        allLines = json.load(f)
                        if "shaders" in allLines:
                            cacheAssignations.addShaders(allLines["shaders"], fromFile=True)
                        if "overrides" in allLines:
                            cacheAssignations.addOverrides(allLines["overrides"], fromFile=True)
                        if "displacement" in allLines:
                            cacheAssignations.addDisplacements(allLines["displacement"], fromFile=True)
                        if "layers" in allLines:
                            cacheAssignations.addLayers(allLines["layers"], fromFile=True)
                        f.close()
                    except:
                        pass


                if not cmds.objExists(str(shape) + ".shadersAssignation"):
                    cmds.addAttr(shape, ln='shadersAssignation', dt='string')
                else:
                    cur = cmds.getAttr("%s.shadersAssignation"  % shape)
                    if cur != None and cur != "":
                        try:
                            cacheAssignations.addShaders(json.loads(cur))
                        except:
                            pass


                if not cmds.objExists(str( shape )+ ".attributes"):
                    cmds.addAttr(shape, ln='attributes', dt='string')

                else:
                    cur = cmds.getAttr("%s.attributes"  % shape)
                    if cur != None and cur != "":
                        try:
                            cacheAssignations.addOverrides(json.loads(cur))
                        except:
                            pass


                if not cmds.objExists(str(shape) + ".displacementsAssignation"):
                    cmds.addAttr(shape, ln='displacementsAssignation', dt='string')
                else:
                    cur = cmds.getAttr("%s.displacementsAssignation" % shape)
                    if cur != None and cur != "":
                        try:
                            cacheAssignations.addDisplacements(json.loads(cur))
                        except:
                            pass


                if not cmds.objExists(str(shape) + ".layersOverride"):
                    cmds.addAttr(shape, ln='layersOverride', dt='string')
                else:
                    cur = cmds.getAttr("%s.layersOverride"  % shape)
                    if cur != None and cur != "":
                        try:
                            cacheAssignations.addLayers(json.loads(cur))
                        except:
                            pass

                attrs=["Json","Shaders","Overrides","Displacements"]
                for attr in attrs:
                    if not cmds.objExists(str(shape) + ".skip%s" % attr):
                        cmds.addAttr(shape, ln='skip%s' % attr, at='bool')

    def getCache(self):
        for shape in self.ABCViewerNode:
            self.ABCViewerNode[shape].updateCache()


    def createWildCard(self, parentItem, wildcard="*", protected=False) :
        ''' Create a wilcard assignation item '''

        newItem = treeitemWildcard.wildCardItem(parentItem.cache, wildcard, self)
        parentItem.cache.itemsTree.append(newItem)
        newItem.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.DontShowIndicator)
        parentItem.addChild(newItem)
        
        newItem.checkShaders(self.getLayer())
        newItem.checkProperties(self.getLayer())

        newItem.protected = protected

    def addWildCard(self):
        ''' Add a widldcard expression to the current cache'''
        
        # first get the current cache
        item = self.hierarchyWidget.currentItem()
        if item is None:
            return

        # and the top level ancestor..
        if item is not None:
            while 1:
                pitem = item.parent()
                if pitem is None:
                    break
                item = pitem

        self.createWildCard(item)
