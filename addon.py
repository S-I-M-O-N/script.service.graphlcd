#  Graphlcd Addon for Kodi
#  Copyright (C) 2016 Manuel Reimer <manuel.reimer@gmx.de>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import xbmc
import xbmcaddon
import xbmcgui
import string

addon         = xbmcaddon.Addon()
resourcespath = xbmc.translatePath(addon.getAddonInfo('path')) + '/resources'

sys.path.insert(0, resourcespath + '/lib')
import graphlcd
import channelsalias


def NotifyError(aMessage):
  xbmcgui.Dialog().notification("Graphlcd", aMessage, xbmcgui.NOTIFICATION_ERROR)
def NotifyInfo(aMessage):
  xbmcgui.Dialog().notification("Graphlcd", aMessage, xbmcgui.NOTIFICATION_INFO)
def LogInfo(aMessage):
  xbmc.log("Graphlcd: " + aMessage)
def LogDebug(aMessage):
  xbmc.log("Graphlcd: " + aMessage, xbmc.LOGDEBUG)


# http://kodi.wiki/view/Window_IDs
class WINDOW_IDS:
  WINDOW_HOME                  = 10000
  WINDOW_VIDEO_NAV             = 10025
  WINDOW_MUSIC_NAV             = 10502
  WINDOW_FULLSCREEN_VIDEO      = 12005
  WINDOW_VISUALISATION         = 12006
  WINDOW_TV_CHANNELS_OLD       = 10615 # Jarvis
  WINDOW_TV_RECORDINGS_OLD     = 10616
  WINDOW_RADIO_CHANNELS_OLD    = 10620
  WINDOW_TV_CHANNELS           = 10700
  WINDOW_TV_RECORDINGS         = 10701
  WINDOW_RADIO_CHANNELS        = 10705

# Returns "cleaned up" volume value as plain integer from 0 (min) to 60 (max)
def GetPlayerVolume():
  return 60 + int(float(string.replace(string.replace(xbmc.getInfoLabel('Player.Volume'), ',', '.'), ' dB', '')))


# Returns the name of the screen which should appear on the LCD in Kodi's
# current state
def GetCurrentScreenName():
  windowid = xbmcgui.getCurrentWindowId()
  LogDebug('Window ID: ' + str(windowid))
  LogDebug('NumItems: ' + xbmc.getInfoLabel('Container.NumItems'))

  if windowid == WINDOW_IDS.WINDOW_HOME:
    return 'navigation'
  if windowid == WINDOW_IDS.WINDOW_MUSIC_NAV or \
     windowid == WINDOW_IDS.WINDOW_VIDEO_NAV or \
     windowid == WINDOW_IDS.WINDOW_TV_CHANNELS_OLD or \
     windowid == WINDOW_IDS.WINDOW_TV_RECORDINGS_OLD or \
     windowid == WINDOW_IDS.WINDOW_RADIO_CHANNELS_OLD or \
     windowid == WINDOW_IDS.WINDOW_TV_CHANNELS or \
     windowid == WINDOW_IDS.WINDOW_TV_RECORDINGS or \
     windowid == WINDOW_IDS.WINDOW_RADIO_CHANNELS:
    return 'menu'
  if windowid == WINDOW_IDS.WINDOW_VISUALISATION or \
     windowid == WINDOW_IDS.WINDOW_FULLSCREEN_VIDEO:
    if xbmc.getCondVisibility('Pvr.IsPlayingTv') or \
       xbmc.getCondVisibility('Pvr.IsPlayingRadio'):
      return 'tvshow'
    else:
      return 'replay'
  else:
    return 'navigation'

# Returns name of the screen which is to be drawn above the current main screen
# Currently only for the "volume" overlay
def GetCurrentOverlayName():
  volume = GetPlayerVolume()
  if not hasattr(GetCurrentOverlayName, 'lastvolume'):
    GetCurrentOverlayName.lastvolume = volume

  if GetCurrentOverlayName.lastvolume != volume or \
     xbmc.getCondVisibility('Player.Muted'):
    GetCurrentOverlayName.lastvolume = volume
    return 'volume'
  else:
    return ''


# The C(++) part calls into this callback function to get values for token names
def GetTokenValue(aVariableName, aAttrib, aIndex, aMaxItems):
  # Kodi "Builtins" (Prefixed with "Info." or "Bool.")
  if aVariableName.startswith('Info.'):
    if aAttrib != '':
      return xbmc.getInfoLabel(aVariableName[5:] + '(' + aAttrib + ')')
    else:
      return xbmc.getInfoLabel(aVariableName[5:])
  elif aVariableName.startswith('Bool.'):
    return xbmc.getCondVisibility(aVariableName[5:])

  # Volume level variables
  elif aVariableName == 'VolumeCurrent':
    return GetPlayerVolume()
  elif aVariableName == 'VolumeTotal':
    return 60

  # Playback times
  elif aVariableName == 'PlayerDuration':
    try: return int(xbmc.Player().getTotalTime())
    except: return ''
  elif aVariableName == 'PlayerTime':
    try: return int(xbmc.Player().getTime())
    except: return ''

  # Scroll settings
  elif aVariableName == 'ScrollMode' or \
       aVariableName == 'ScrollSpeed' or \
       aVariableName == 'ScrollTime':
    return addon.getSetting(aVariableName.lower())

  # Channel alias
  elif aVariableName == 'ChannelAlias':
    return channelsalias.GetChannelAlias(xbmc.getInfoLabel('VideoPlayer.ChannelName'))

  # Menu variables
  elif aVariableName == 'MenuItem' or \
       aVariableName == 'IsMenuCurrent':
    infolabelcuritem = xbmc.getInfoLabel('Container.CurrentItem')
    infolabelnumitems = xbmc.getInfoLabel('Container().NumItems')
    # Empty values happen if the menu is closing or opening.
    if infolabelcuritem == '' or infolabelnumitems == '':
      return ''
    osdCurrentItemIndex = int(infolabelcuritem) - 1
    osdItemsSize = int(infolabelnumitems)

    # "Folder lists" have a leading ".." item.
    if xbmc.getCondVisibility('Container.HasParent'):
      osdCurrentItemIndex += 1
      osdItemsSize += 1

    if osdItemsSize == 0:
      return ''

    maxItems = aMaxItems
    if maxItems > osdItemsSize:
      maxItems = osdItemsSize

    currentIndex = maxItems / 2
    if (osdCurrentItemIndex < currentIndex):
      currentIndex = osdCurrentItemIndex

    topIndex = osdCurrentItemIndex - currentIndex
    if (topIndex + maxItems) > osdItemsSize:
      currentIndex += (topIndex + maxItems) - osdItemsSize
      topIndex = osdCurrentItemIndex - currentIndex

    if aVariableName == 'MenuItem':
      if aIndex < maxItems:
        return xbmc.getInfoLabel('Container().ListItemAbsolute(' + str(topIndex + aIndex) + ').Label')

    if aVariableName == 'IsMenuCurrent':
      if aIndex < maxItems and aIndex == currentIndex:
        return 1

    return ''

  else:
    LogInfo('Invalid variable name requested: ' + aVariableName + "\n")
    return ''

if __name__ == '__main__':
  graphlcd.SetResourcePath(resourcespath)

  channelsalias.Load(resourcespath + '/channels.alias')

  loaded_driver = ""
  loaded_skin = ""
  config_loaded = 0
  current_brightness = -1
  wait_time = 0.1
  monitor = xbmc.Monitor()
  while not monitor.abortRequested():
    if monitor.waitForAbort(wait_time):
      break
    wait_time = 0.5

    # Try to load config if not already done
    if not config_loaded:
      LogInfo("Loading config")
      try:
        graphlcd.ConfigLoad()
        config_loaded = 1
      except IOError:
        NotifyError("Failed to read /etc/graphlcd.conf")
        wait_time = 7
        continue

    # Load driver
    driver_setting = addon.getSetting('driver')
    if loaded_driver != driver_setting:
      loaded_driver = ""
      LogInfo("Loading driver")
      try:
        graphlcd.CreateDriver(driver_setting)
        loaded_driver = driver_setting
        loaded_skin = "" # Reload skin if driver has changed!
      except NameError:
        NotifyError("No display with name " + driver_setting + " defined in /etc/graphlcd.conf")
        wait_time = 7
        continue
      except IOError:
        NotifyInfo("Failed to access LCD " + driver_setting)
        wait_time = 7
        continue

    # Load skin
    skin_setting = addon.getSetting('skin')
    if loaded_skin != skin_setting:
      loaded_skin = ""
      LogInfo("Loading skin")
      try:
        graphlcd.ParseSkin(skin_setting)
        loaded_skin = skin_setting
      except IOError:
        NotifyError("Skin file for Skin " + skin_setting + " does not exist!")
        wait_time = 7
        continue
      except SyntaxError:
        NotifyError("Parsing of Skin failed. Check Kodi log file!")
        wait_time = 7
        continue

    # Set brightness
    brightness_setting = 0
    if xbmc.getCondVisibility('System.ScreenSaverActive'):
      brightness_setting = int(addon.getSetting('brightness_screensave'))
    else:
      brightness_setting = int(addon.getSetting('brightness'))
    if current_brightness != brightness_setting:
      LogInfo("Setting brightness")
      graphlcd.SetBrightness(brightness_setting)
      current_brightness = brightness_setting

    # Render display
    graphlcd.Render(GetCurrentScreenName(), GetCurrentOverlayName(), GetTokenValue)


  # Before stopping Addon, send the "shutdown screen" to the LCD.
  # Only do this if display and skin are loaded.
  # Use a lambda callback to prevent calling back into Kodi while shutting down
  if loaded_skin:
    graphlcd.Render('shutdown', '', lambda x1, x2, x3, x4: 0)

  # Finally shutdown graphlcd
  graphlcd.Shutdown()
