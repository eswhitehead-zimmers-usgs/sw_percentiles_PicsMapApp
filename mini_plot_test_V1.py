# -*- coding: utf-8 -*-
"""
This script tries to getting a working proof-of-concept for Brandon's idea
to have mini distribution plots laid over each watershed on a map
test case: Fishing Creek near Bloomsburg, PA
            01539000

Eli Whitehead-Zimmers
1.17.24
"""

# Import packages
import geopandas as gp
# needed to: pip install --upgrade shapely==1.8.4
import os
import folium as fl
from streamlit_folium import st_folium
import streamlit as st
import pandas as pd
import plotly.express as px

# Define functions
def load_dat():
# This function loads in surface water percentile trends for all sites
# Input:
    # Just requires having the sw_trends_all_sites.csv
# Output:
    # 1. trends_all_sites: percentile trends for all sites in deleware river basin
    # 2. drb_watersheds: polygons for the huc8 deleware river basin watersheds 
    # 3. site_list: manually compiled list of site names with their lat and longs
        # that we want to be plotted on the map
    
    
    trends_all_sites = pd.read_csv(r"sw_trends_all_sites.csv",
                                   index_col = 0,
                                   dtype = {"site_no": "string"})
    
    # Deleware river watershed boundaries: https://www.nj.gov/drbc/basin/map/GIS.html
    drb_watersheds = gp.read_file("drb147.shp")
    
    # In this version, hand select sites you want to display on the map
    site_nms = "BEAVER KILL AT COOKS FALLS NY|Brodhead Creek at Minisink Hills, PA|Little Neshaminy C at Valley Road nr Neshaminy PA|RED CLAY CREEK NEAR STANTON, DE|Maurice River at Norma NJ"
    site_list = trends_all_sites[trends_all_sites['station_nm'].str.contains(site_nms)]
    site_list = site_list[['station_nm','lat','long']].drop_duplicates(subset=['station_nm'])

    return trends_all_sites, drb_watersheds, site_list

def plot_dat(trends_all_sites, station_nm):
# This function plots mann-kendall slope for each percentile of a given site
# Input:
    # trends_all_sites: variable containing all trends for all 76 sites
    # station_nm: name of the site you want plotted (names are stored within trends_all_sites)
# Output:
    # 1. bar_fig: Percentile trends plotted as a bar graph to better 
    # visually show the distribution of trends across percentiles (because
    # these plots are placed onto a map as a raster)
      
    # filter out which specific site you want to plot
    trends_all_sites_plt = trends_all_sites[trends_all_sites['station_nm'] == station_nm]
       
    # Create discrete color map
    color_discrete_map = {'increasing': '#d62728',
                          'decreasing': '#1f77b4',
                          'no trend': '#7f7f7f'}
        
    # Create plotly bar graph:
    bar_fig = px.bar(trends_all_sites_plt,
                     x = "percentile",
                     y = "slope",
                     color = "Trend",
                     color_discrete_map = color_discrete_map)
                     #template='simple_white',
                     #title = station_nm)
    
    # Simplify graph so we get just the main idea (because this will be displayed
    # on our map and it will be tiny, so just get the main ideas across)
    #bar_fig.update_layout(showlegend=False)
    #bar_fig.update_xaxes(visible=False)
    #bar_fig.update_yaxes(visible=False)
    #bar_fig.update_layout(autosize = True)
    
    bar_fig.update_layout(
        title_text=station_nm, 
        yaxis=dict(title='slope of trend (%)'),
        xaxis=dict(title='Groundwater Level Percentile'),
        autosize = True)


    return(bar_fig)

def map_dat():
    # This function creates and customizes the folium map where raster 
    # and polygon data will be overlayed
    # Input - none
    # Output:
        # 1. m: handle for the map object
    # Create interactive map
    m = fl.Map(location=[40.9, -75], zoom_start=6.55)

    # Add fullscreen button
    fl.plugins.Fullscreen(
        position="topright",
        title="Expand me",
        title_cancel="Exit me",
        force_separate_button=True,
    ).add_to(m)
    
    return(m)

def polygon_dat(drb_watersheds, m):
# This function adds watershed shapefiles to our basemap
# Input
    # 1. drb_watersheds: geopandas data frame with geometries of the watershed
        # drb = delaware river basin
    # 2. the folium map that we are adding the shapefiles to 
# Output
    # 1. the folium map that has the new shapefiles added on 
    
    # Fix polygon projection to the projection of folium maps
    drb_watersheds = drb_watersheds.to_crs(epsg=3857)
    
    # Add shapefiles to the map
    fl.GeoJson(data=drb_watersheds.geometry).add_to(m)
    
    # Extra features if we want to mess around with them later
        #geo_j = drb_watersheds.to_json()
        #geo_j = fl.GeoJson(data=geo_j, style_function=lambda x: {"fillColor": "orange"})
        #geo_j.add_to(m)
    
    return(m)

def rast_dat(fig, m, site_list, station_nm,i):
# This function creates a png from a plotly graph and adds it to our basemap
# as a raster. Each png is centered around the site for which it was created
# Input
    # 1. fig: The plotly object that you want to turn into a png and overlay on the map
    # 2. m: basemap that you 
    # 3. site_list: list of manually selected sites with lat longs
    # 4. station_nm: name of the individual station we are looping though
    # 5. i: iteration of the loop we are on. this is concatenated into file
        # location strings
# Output
    # 1. m: returns our folium map with a new figure overlayed as a raster
    
    
    # Following line is commented out. I used it only once to generate the plots. Streamlit
    # won't let me write files from their cloud, so I had to make them before deploying
    # app.
    #file_loc = "Data\\bar_fig" + str(i) + ".png"
    #fig.write_image(file_loc)
    


    image_path = "bar_fig" + str(i) + ".png" 

    # Overlay .png on the map
    fl.raster_layers.ImageOverlay(
        image=image_path,
        bounds=[[site_list[site_list['station_nm'].str.contains(station_nm)].lat.iloc[0] - .15, # Define bottom left corner
                 site_list[site_list['station_nm'].str.contains(station_nm)].long.iloc[0] - .2], 
                
                [site_list[site_list['station_nm'].str.contains(station_nm)].lat.iloc[0] + .15, # Define top right corner
                 site_list[site_list['station_nm'].str.contains(station_nm)].long.iloc[0] + .2]],   
        colormap=lambda x: (1, 0, 0, x),
    ).add_to(m)
    
    #m.keep_in_front("ImageOverlay")
    
    return(m)




### App Layout ###
# Adjust layout to take up full width of screen
st.set_page_config(layout="wide")

# Add Title
'''
# Discharge Trends for Streams in Delaware River Basin
'''


### LOAD IN DATA ###
# Trends data
trends_all_sites, drb_watersheds, site_list = load_dat()


### CREATE INTERACTIVE MAP ###
# create base map
m = map_dat()

# Add watersheds to the map
#m = polygon_dat(drb_watersheds, m)

# Add site plots to basemap
i = 1
for station_nm in site_list.station_nm:
    # Create plot to put on map
    bar_fig = plot_dat(trends_all_sites, station_nm)
    
    # Save plot and put it onto the map
    m = rast_dat(bar_fig, m, site_list, station_nm,i)
    i = i+1


# This produces the map in streamlit. This HAS TO COME AFTER THE MAP IS FINISHED
gw = st_folium(m, use_container_width = True)


