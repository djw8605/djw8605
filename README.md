Derek Weitzel
=============

I am a research assistant professor at the University of Nebraska-Lincoln.

I program in many languages:
<p>
<img alt="python" src="https://img.shields.io/badge/-Python-4B8BBE?style=flat-square&logo=python&logoColor=white" />
<img alt="git" src="https://img.shields.io/badge/-Git-F05032?style=flat-square&logo=git&logoColor=white" />
<img alt="Go" src="https://img.shields.io/badge/-Go-29BEB0?style=flat-square&logo=go&logoColor=white" />
<img alt="Kubernetes" src="https://img.shields.io/badge/-Kubernetes-326CE5?style=flat-square&logo=kubernetes&logoColor=white" />
<img alt="Heroku" src="https://img.shields.io/badge/-Heroku-430098?style=flat-square&logo=heroku&logoColor=white" />
<img alt="Docker" src="https://img.shields.io/badge/-Docker-46a2f1?style=flat-square&logo=docker&logoColor=white" />
<img alt="Nodejs" src="https://img.shields.io/badge/-Nodejs-43853d?style=flat-square&logo=Node.js&logoColor=white" />
<img alt="html5" src="https://img.shields.io/badge/-HTML5-E34F26?style=flat-square&logo=html5&logoColor=white" />
<img alt="reactjs" src="https://img.shields.io/badge/-React-61DAFB?style=flat-square&logo=React&logoColor=black" />
<img alt="nextjs" src="https://img.shields.io/badge/-Next.js-000000?style=flat-square&logo=Next.js&logoColor=white" />

</p>

![Derek's GitHub stats](https://github-readme-stats.vercel.app/api?username=djw8605&show_icons=true)


Latest [blog](https://derekweitzel.com) posts
----------------------------------------------

<ul>

<li><a href="https://derekweitzel.com/2024/01/31/profiling-xrootd-collector/">Profiling the XRootD Monitoring Collector</a><br/><p>The <a href="https://github.com/opensciencegrid/xrootd-monitoring-collector">XRootD Monitoring Collector</a> (collector) receives file transfer accounting messages from <a href="https://xrootd.slac.stanford.edu/">XRootD</a> servers.
This transfer information is parsed by the collector and sent to the GRACC accounting database for visualization.
Each transfer will generate multiple messages:</p>

<ol>
  <li>Connection message with client information</li>
  <li>Token information</li>
  <li>File open with file name</li>
  <li>Transfer updates (potentially multiple)</li>
  <li>File close with statistics about bytes read and written</li>
  <li>Disconnection</li>
</ol>

<p>We can see 1000+ messages a second from XRootD servers across the OSG.  But, recently the collector has not been able to keep up.  Below is the traffic of messages to the collector from the OSG’s Message Bus:</p>

<figure class="">
  <img alt="this is a placeholder image" src="https://derekweitzel.com/images/posts/profiling-xrootd-collector/before-optimization-mq.png" /><figcaption>
      Message bus traffic before optimization

    </figcaption></figure>

<p>The graph is from the message bus’s perspective, so publish is incoming to the message bus, and deliver is sending to consumers (the Collector).  We are receiving (Publish) ~1550 messages a second, while the collector is only able to process (Deliver) ~500 messages a second.  1550 messages a second is higher than our average, but we need to be able to process data as fast as it comes.  Messages that are not processed will wait on the queue.  If the queue gets too large (maximum is set to 1 Million messages) then the messages will be deleted, losing valuable transfer accounting data.  At a defecit 1000 messages a second, it would only take ~16 minutes to fill the queue.  It is clear that we missed data for a significant amount of time.</p>

<h2 id="profiling">Profiling</h2>

<p>The first step to optimizing the XRootD Monitoring Collector is to profile the current process.  Profiling is the process of measuring the performance of the collector to identify bottlenecks and areas for improvement.</p>

<p>For profiling, I created a development environment on the <a href="https://nationalresearchplatform.org/">National Research Platform (NRP)</a> to host the collector.  I started a <a href="https://docs.nationalresearchplatform.org/userdocs/jupyter/jupyterhub-service/">jupyter notebook on the NRP</a>, and used VSCode to edit the collector code and a Jupyter notebook to process the data.  I used the <a href="https://docs.python.org/3/library/profile.html">cProfile</a> package built into python to perform the profiling.
I modified the collector to output a profile update every 10 seconds so I could see the progress of the collector.</p>

<p>After profiling, I used <a href="https://jiffyclub.github.io/snakeviz/">snakeviz</a> to visualize the profile.  Below is a visualization of the profile before any optimization.  The largest consumer of processing time was DNS resoluiton, highlighted in the below image in purple.</p>

<figure class="">
  <img alt="this is a placeholder image" src="https://derekweitzel.com/images/posts/profiling-xrootd-collector/before-optimization-profile.png" /><figcaption>
      Snakeviz profile.  Purple is the DNS resolution function

    </figcaption></figure>

<p>The collector uses DNS to resolve the hostnames for all IPs it receives in order to provide a human friendly name for clients and servers.  Significant DNS resolution is expected as the collector is receiving messages from many different hosts.  However, the DNS resolution is taking up a significant amount of time and is a bottleneck for the collector.</p>

<h2 id="improvement">Improvement</h2>

<p>After reviewing the profile, <a href="https://github.com/opensciencegrid/xrootd-monitoring-collector/pull/43">I added a cache to the DNS resolution</a> so that the collecotr only needs to resolve the host once every 24 hours.  When I profiled after making the change, I saw a significant improvement in DNS resolution time.  Below is another visualization of the profile after the DNS caching, purple is the DNS resolution.</p>

<figure class="">
  <img alt="this is a placeholder image" src="https://derekweitzel.com/images/posts/profiling-xrootd-collector/after-optimization-profile.png" /><figcaption>
      Snakeviz profile.  Purple is the DNS resolution function

    </figcaption></figure>

<p>Notice that the DNS resolution is a much smaller portion of the overall running time when compared to the previous profile.</p>

<p>In the following graph, I show the time spent on DNS resolution over time for both before and after the optimization.  I would expect DNS resolution to increase for both, but as you can see, the increase after adding DNS caching is much slower.</p>

<figure class="">
  <img alt="this is a placeholder image" src="https://derekweitzel.com/images/posts/profiling-xrootd-collector/dns-resolution.png" /><figcaption>
      Growth of DNS resolution time

    </figcaption></figure>

<h2 id="production">Production</h2>

<p>When we applied the changes into production, we saw a significant improvement in the collector’s ability to process messages.  Below is the graph of the OSG’s Message Bus after the change:</p>

<figure class="">
  <img alt="this is a placeholder image" src="https://derekweitzel.com/images/posts/profiling-xrootd-collector/edited-production-mq.png" /><figcaption>
      RabbitMQ Message Parsing

    </figcaption></figure>

<p>The incoming messages decreased, but the collector is now able to process messages as fast as they are received.  This is a significant improvement over the previous state.  I suspect that the decrease in incoming messages is due to server load of sending more outgoing messages to the improved collector.  The message bus can slow down the incoming messages under heavier load.</p>

<h2 id="conclusions-and-future-work">Conclusions and Future Work</h2>

<p>Since we implemented the cache for DNS resolution, the collector has been able to keep up with the incoming messages.  This is a significant improvement over the previous state.  Over time, we expect the DNS cache to capture nearly all of the hosts, and the DNS resolution time to decrease even further.</p>

<p>We continue to look for optimizations to the collector.  When looking at the output from the most recent profile, we noticed the collector is spending a significant amount of time in the logging functions.  By default, we have debug logging turned on.  We will look at turning off debug logging in the future.</p>

<p>Additionally, the collector is spending a lot of time polling for messages.  In fact, the message bus is receiving ~1500 messages a second, which is increasing the load on the message bus.  After reading through optimizations for RabbitMQ, it appears that less but larger messages are better for the message bus.  We will look at batching messages in the future.</p></li>

<li><a href="https://derekweitzel.com/2022/09/14/dashboards/">Dashboards for Learning Data Visualizations</a><br/><p>Creating dashboards and data visualizations are a favorite past time of mine.  Also, I jump at any chance to learn a new technology.  That is why I have spent the last couple of months building dashboards and data visualizations for various projects while learning several web technologies.</p>

<p>Through these dashboards, I have learned many new technologies:</p>
<ul>
  <li><a href="https://reactjs.org/">React</a> and <a href="https://nextjs.org/">NextJS</a></li>
  <li>Mapping libraries such as <a href="https://leafletjs.com/">Leaflet</a> and <a href="https://www.mapbox.com/">Mapbox</a></li>
  <li>CSS libraries such as <a href="https://derekweitzel.com/2022/09/14/dashboards/TailwindCSS">TailwindCSS</a></li>
  <li>Data access JS clients for <a href="https://derekweitzel.com/2022/09/14/dashboards/Elasticsearch">Elasticsearch</a> and <a href="https://derekweitzel.com/2022/09/14/dashboards/Prometheus">Prometheus</a></li>
  <li>Website hosting service <a href="https://derekweitzel.com/2022/09/14/dashboards/Vercel">Vercel</a></li>
  <li>Data Visualization library <a href="https://derekweitzel.com/2022/09/14/dashboards/D3.js">D3.js</a></li>
</ul>

<h2 id="gp-argo-dashboard"><a href="https://gp-argo.greatplains.net/">GP-ARGO Dashboard</a></h2>

<p><a href="https://gp-argo.greatplains.net/">The Great Plains Augmented Regional Gateway to the Open Science Grid</a> (GP-ARGO) is a regional collaboration of 16 campuses hosting computing that is made available to the OSG.  My goal with the GP-ARGO dashboard was to show who is using the resources, as well as give high level overview of the region and sites hosting GP-ARGO resources.</p>

<p>The metrics are gathered from OSG’s <a href="https://gracc.opensciencegrid.org/">GRACC Elasticsearch</a>.  The list of projects are also from GRACC, and the bar graph in the bottom right are from OSG is simply an iframe to a grafana panel from GRACC.</p>

<p>Technologies used: <a href="https://reactjs.org/">React</a>, <a href="https://nextjs.org/">NextJS</a>, <a href="https://leafletjs.com/">Leaflet</a>, <a href="https://github.com/elastic/elasticsearch-js">Elasticsearch</a></p>

<p><strong>Repo:</strong> <a href="https://github.com/djw8605/gp-argo-map">GP-ARGO Map</a></p>

<p><a href="https://gp-argo.greatplains.net/"><img alt="GP-ARGO" src="https://derekweitzel.com/images/posts/Dashboards/gp-argo-screenshot.png" /></a></p>

<h2 id="osdf-website"><a href="https://osdf.osg-htc.org/">OSDF Website</a></h2>

<p>My next website was the <a href="https://osdf.osg-htc.org/">Open Science Data Federation</a> landing page.  I was more bold in the design of the OSDF page.  I took heavy inspiration from other technology websites such as the <a href="https://www.mapbox.com/">Mapbox</a> website and the <a href="https://k8slens.dev/">Lens</a> website.  The theme is darker and it was also my first experience with the TailwindCSS library.  Additionally, I learned the CSS <a href="https://en.wikipedia.org/wiki/CSS_Flexible_Box_Layout">flexbox</a> layout techniques.</p>

<p>The spinning globe is using the <a href="https://globe.gl/">Globe.gl</a> library.  The library is great to create visualizations to show distribution throughout the world.  On the globe I added “transfers” between the OSDF origins and caches.  Each origin sends transfers to every cache in the visualization, though it’s all just animation.  There is no data behind the transfers, it’s only for visual effect.  Also, on the globe, each cache location is labeled.  The globe can be rotated and zoomed with your mouse.</p>

<p>The number of bytes read and files read is gathered using the Elasticsearch client querying GRACC, the OSG’s accounting service.  The OSG gathers statistics on every transfer a cache or origin perform.  Additionally, we calculate the rate of data transfers and rate of files being read using GRACC.</p>

<p>One unique feature of the OSDF website is the resiliency of the bytes read and files read metrics.  We wanted to make sure that the metrics would be shown even if a data component has failed.  The metrics are gathered in 3 different ways for resiliency:</p>
<ol>
  <li>If all components are working correctly, the metrics are downloaded from the OSG’s Elasticsearch instance.</li>
  <li>If OSG Elasticsearch has failed, the dashboard pulls saved metrics from NRP’s S3 storage.  The metrics are saved everytime they are succesfully gathered from Elasticsearch, so they should be fairly recent.</li>
  <li>The metrics are gathered and saved on each website build.  The metrics are static and immediatly available upon website load.  If all else fails, these saved static metrics are always available, even if they may be old.</li>
</ol>

<p>Technologies used: <a href="https://reactjs.org/">React</a>, <a href="https://nextjs.org/">NextJS</a>, <a href="https://globe.gl/">Globe.gl</a></p>

<p><strong>Repo:</strong> <a href="https://github.com/djw8605/osdf-website">OSDF Website</a></p>

<p><a href="https://osdf.osg-htc.org/"><img alt="OSDF" src="https://derekweitzel.com/images/posts/Dashboards/osdf-screenshot.png" /></a></p>

<h2 id="nrp-dashboard"><a href="https://dash.nrp-nautilus.io/">NRP Dashboard</a></h2>

<p>The National Research Platform dashboard is largely similar to the <a href="https://derekweitzel.com/2022/09/14/dashboards/#gp-argo-dashboard">GP-ARGO</a> dashboard.  It uses the same basic framework and technologies.  But, the data acquisition is different.</p>

<p>The metrics shown are the number of gpus allocated, number of pod running, and the number of active research groups.  The metrics are gathered from the NRP’s <a href="https://prometheus.io/">prometheus</a> server on-demand.  The graph in the background of the metric is generated with <a href="https://d3js.org/">D3.js</a>.</p>

<p>Technologies used: <a href="https://reactjs.org/">React</a>, <a href="https://nextjs.org/">NextJS</a>, <a href="https://d3js.org/">D3.js</a>, <a href="https://github.com/siimon/prom-client">Prometheus</a>, <a href="https://tailwindcss.com/">TailwindCSS</a></p>

<p><strong>Repo:</strong> <a href="https://github.com/djw8605/nrp-map-app">NRP Map App</a></p>

<p><a href="https://dash.nrp-nautilus.io/"><img alt="NRP Dashboard" src="https://derekweitzel.com/images/posts/Dashboards/nrp-dashboard-screenshot.png" /></a></p>

<h2 id="pnrp-website"><a href="https://nrp-website.vercel.app/">PNRP Website</a></h2>

<p>The <a href="https://www.nsf.gov/awardsearch/showAward?AWD_ID=2112167&amp;HistoricalAwards=false">Prototype National Research Platform</a> is a NSF research platform.  The dashboard is also in prototype stage as the PNRP hardware is not fully delivered and operational yet.</p>

<p>The dashboard is my first experience with a large map from <a href="https://www.mapbox.com/">Mapbox</a>.  I used a <a href="https://visgl.github.io/react-map-gl/">React binding</a> to interface with the <a href="https://www.mapbox.com/">Mapbox</a> service.  Also, when you click on a site, it zooms into the building where the PNRP hardware will be hosted.</p>

<p>The transfer metrics come from the NRP’s prometheus which shows the bytes moving into and out of the node.  The transfer metrics are for cache nodes nearby the sites, but once PNRP hardware becomes operational the transfer metrics will show the site’s cache.</p>

<p>Technologies Used: <a href="https://reactjs.org/">React</a>, <a href="https://nextjs.org/">NextJS</a>, <a href="https://www.mapbox.com/">Mapbox</a>, <a href="https://tailwindcss.com/">TailwindCSS</a>, <a href="https://github.com/siimon/prom-client">Prometheus</a></p>

<p><strong>Repo:</strong> <a href="https://github.com/djw8605/nrp-website">NRP Website</a></p>

<p><a href="https://nrp-website.vercel.app/"><img alt="PNRP Website" src="https://derekweitzel.com/images/posts/Dashboards/nrp-website-screenshot.png" /></a></p></li>

<li><a href="https://derekweitzel.com/2022/01/22/improving-geoip/">Improving the Open Science Data Federation’s Cache Selection</a><br/><p>Optimizing data transfers requires tuning many parameters.  High latency between the client and a server can decrease data transfer throughput. The Open Science Data Federation (OSDF) attempts to optimize the latency between a client and cache by using GeoIP to locate the nearest cache to the client.  But, using GeoIP alone has many flaws.  In this post, we utilize <a href="https://workers.cloudflare.com/">Cloudflare Workers</a> to provide GeoIP information during cache selection.  During the evaluation, we found that location accuracy grew from <strong>86%</strong> accurate with the original GeoIP service to <strong>95%</strong> accurate with Cloudflare Workers.</p>

<figure class="">
  <img alt="Map of U.S. OSDF" src="https://derekweitzel.com/images/posts/CloudflareWorkers/CacheMap.png" /><figcaption>
      Map of OSDF locations

    </figcaption></figure>

<p>GeoIP has many flaws, first, the nearest physical cache may not be the nearest in the network topology.  Determining the nearest cache in the network would require probing the network topology between the client and every cache, a intensive task to perform for each client startup, and may be impossible with some network configurations, such as blocked network protocols.</p>

<p>Second, the GeoIP database is not perfect.  It does not have every IP address, and the addresses may not have accurate location information.  When GeoIP is unable to determine a location, it will default to “guessing” the location is a lake in Kansas (<a href="https://arstechnica.com/tech-policy/2016/08/kansas-couple-sues-ip-mapping-firm-for-turning-their-life-into-a-digital-hell/">a well known issue</a>).</p>

<p>Following a review of the Open Science Data Federation (OSDF), we found that we could improve effeciency by improving the geo locating of clients.  In the review, several sites where detected to not be using the nearest cache.</p>

<h2 id="implementation">Implementation</h2>

<p>StashCP queries the <a href="https://cernvm.cern.ch/fs/">CVMFS</a> geo location service which relies on the <a href="https://www.maxmind.com/en/home">MaxMind GeoIP database</a>.</p>

<p><a href="https://workers.cloudflare.com/">Cloudflare Workers</a> are designed to run at Cloudflare’s many colocation facilities near the client.  Cloudflare directs a client’s request to a nearby data center using DNS.  Each request is annotaed with an approximate location of the client, as well as the colocation center that received the request.  Cloudflare uses a GeoIP database much like MaxMind, but it also falls back to the colocation site that the request was serviced.</p>

<p>I wrote a Cloudflare worker, <a href="https://github.com/djw8605/cache-locator"><code class="language-plaintext highlighter-rouge">cache-locator</code></a>, which calculates the nearest cache to the client.  It uses the GeoIP location of the client to calculate the ordered list of nearest caches.  If the GeoIP fails for a location, the incoming request to the worker will not be annotated with the location but will include the <code class="language-plaintext highlighter-rouge">IATA</code> airport code of the colocation center that received the client request.  We then return the ordered list of nearest caches to the airport.</p>

<p>We imported a <a href="https://www.partow.net/miscellaneous/airportdatabase/">database of airport codes</a> to locations that is pubically available.  The database is stored in the <a href="https://developers.cloudflare.com/workers/learning/how-kv-works">Cloudflare Key-Value</a>, keyed by the <code class="language-plaintext highlighter-rouge">IATA</code> code of the airport.</p>

<h2 id="evaluation">Evaluation</h2>

<p>To evaluate the location, I submitted test jobs to each site available in the OSG OSPool, 43 different sites at the time of evaluation.  The test jobs:</p>

<ol>
  <li>
    <p>Run the existing <code class="language-plaintext highlighter-rouge">stashcp</code> to retrieve the closest cache.</p>

    <div class="language-plaintext highlighter-rouge"><div class="highlight"><pre class="highlight"><code> stashcp --closest
</code></pre></div>    </div>
  </li>
  <li>
    <p>Run a custom <a href="https://github.com/djw8605/closest-cache-cloudflare">closest script</a> that will query the Cloudflare worker for the nearest caches and print out the cache.</p>
  </li>
</ol>

<p>After the jobs completed, I compiled the caches decisions to a <a href="https://docs.google.com/spreadsheets/d/1mo1FHYW2vpCyhSeCCd_bwP21rFFzqedv0dZ0z8EY4gg/edit?usp=sharing">spreadsheet</a> and manually evaluated each cache selection decision.  The site names in the spreadsheet are the somewhat arbitrary internal names given to sites.</p>

<p>In the spreadsheet, you can see that the correct cache was choosen <strong>86%</strong> of the time with the old GeoIP service, and <strong>95%</strong> of the time with Cloudflare workers.</p>

<h3 id="notes-during-the-evaluation">Notes during the Evaluation</h3>

<p>Cloudflare was determined to be incorrect at two sites, the first being <code class="language-plaintext highlighter-rouge">UColorado_HEP</code> (University of Colorado in Boulder).  In this case, the Colorado clients failed the primary GeoIP lookup and the cloudflare workers fell back to using the <code class="language-plaintext highlighter-rouge">IATA</code> code from the request.  The requests from Colorado all where recieved by the Cloudflare Dallas colocation site, which is nearest the Houston cache.  The original GeoIP service choose the Kansas City cache, which is the correct decision.  It is unknown if the orignal GeoIP service choose KC cache because it knew the GeoIP location of the clients, or it defaulted to the Kansas default.</p>

<p>The second site where the Cloudflare worker implementation was incorrect was <code class="language-plaintext highlighter-rouge">SIUE-CC-production</code> (Southern Illinois University Edwardsville).  In this case, the original GeoIP service choose Chicago, while the new service choose Kansas.  Edwardsville is almost equal distance from both the KC cache and Chicago.  The difference in the distance to the caches is ~0.6 KM, with Chicago being closer.</p>

<!-- TODO: Find out why KC cache was choosen SIUE -->

<p>An example of a site that did not work with GeoIP was <code class="language-plaintext highlighter-rouge">ASU-DELL_M420</code> (Arizona Statue University).  The original service returned that the KC cache was the nearest.  The Cloudflare service gave the default Lat/Log if GeoIP failed, the middle of Kansas, but the data center serving the request had the airport code of <code class="language-plaintext highlighter-rouge">LAX</code> (Los Angeles).  The nearest cache to <code class="language-plaintext highlighter-rouge">LAX</code> is the UCSD cache, which is the correct cache decision.</p>

<p>During the evaluation, I originally used the Cloudflare worker development DNS address, <a href="https://stash-location.djw8605.workers.dev">stash-location.djw8605.workers.dev</a>.  Purdue University and the American Museum of Natural History sites both blocked the development DNS address.  The block was from an OpenDNS service which reported the domain had been linked to malware and phishing.  Since the DNS hostname was hours old, it’s likely that most <code class="language-plaintext highlighter-rouge">*workers.dev</code> domains were blocked.</p>

<h2 id="conclusion">Conclusion</h2>

<p>Improving the cache selection can improve the download effeciency.  It is left as future work to measure if the nearest geographical cache is the best choice.  While the OSDF is using GeoIP service for cache selection, it is important to select the correct cache.  Using the new Cloudflare service results in <strong>95%</strong> correct cache decision vs. <strong>86%</strong> with the original service.</p>

<p>Cloudflare Workers is also very affordable for the scale that the OSDF would require.  The first 100,000 requests are free, while it is $5/mo for the next 10 Million requests.  The OSPool runs between 100,000 to 230,000 jobs per day, easily fitting within the $5/mo tier.</p></li>

<li><a href="https://derekweitzel.com/2020/10/11/xrootd-client-manager/">XRootD Client Manager</a><br/><p>The validation project for XRootD Monitoring is moving to phase 2, scale
testing.  Phase 1 focused on correctness of single server monitoring.  <a href="https://doi.org/10.5281/zenodo.3981359">The
report</a> is available.</p>

<p>We are still forming the testing plan for the scale test of XRootD, but a
component of the testing will be multiple clients downloading from multiple
servers.  In addition, we must record exactly how much data each client reads
from each server in order to validate the monitoring with the client’s real behavior.</p>

<p>This level of testing will require detailed coordination and recording of client
actions.  I am not aware of a testing framework that can coordinate and record
accesses of multiple clients and servers, therefore I spent the weekend
developing a simple framework for coordinating these tests.</p>

<p>Some requirements for the application are:</p>

<ul>
  <li>Easy to use interface</li>
  <li>Easy to add clients and servers</li>
  <li>Authenticated access for clients, servers, and interface</li>
  <li>Storage of tests and results</li>
</ul>

<p>I chose <a href="https://heroku.com">Heroku</a> for prototyping this application.</p>

<h2 id="interface">Interface</h2>

<p>The web interface is available at https://xrootd-client-manager.herokuapp.com/.
I chose to host it on heroku as it is my go to for pet projects.  I will likely
move this over to OSG’s production kubernetes installation soon.  The entire
application is only the web interface and a back-end <a href="https://redis.io/">Redis</a>
data store.</p>

<figure class="">
  <img alt="Screenshot of web interface" src="https://derekweitzel.com/images/posts/XRootDClientManager/Interface.png" /><figcaption>
      Screenshot of simple web interface

    </figcaption></figure>

<p>The web interface shows the connected clients and servers.  The web interface
also connects to the web server with an persistent connection to update the list
of connected clients.</p>

<h2 id="client-communication">Client Communication</h2>

<p>Client communcation is handled through a Socket.IO connection.  Socket.IO is a
library that will at create a bi-directional event based communcation between
the client and the server.  The communcation is over websockets if possible, but
will fall back to HTTP long polling.  A good discussion of long polling vs.
websockets is available from
<a href="https://www.ably.io/blog/websockets-vs-long-polling/">Ably</a>.  The Socket.IO
connection is established between each worker, server, and web client and the
web server.</p>

<p>The difficult part is authenticating the Socket.IO connections.  We discuss this
in the security session.</p>

<h2 id="security">Security</h2>
<p>Securing the commands and web interface is required since the web interface is
sending commands to the connected worker nodes and servers.</p>

<h3 id="socketio-connections">Socket.IO Connections</h3>

<p>The Socket.IO connection is secured with a shared key.  The communication flow
for a non-web client (worker/server):</p>

<ol>
  <li>A JWT is created from the secret key.  The secret key is communicated through
a separate secure channel.  In most cases, it will be through the command
line arguments of the client.  The JWT has a limited lifetime and a scope.</li>
  <li>The client registers with the web server, with an Authentication bearer token
in the headers.  The registration includes details about the client.  It
returns a special (secret) <code class="language-plaintext highlighter-rouge">client_id</code> that will be used to authenticate the
Socket.IO connection.  The registration is valid for 30
seconds before the <code class="language-plaintext highlighter-rouge">client_id</code> is no longer valid.</li>
  <li>The client creates a Socket.IO connection with the <code class="language-plaintext highlighter-rouge">client_id</code> in the request
arguments.</li>
</ol>

<h3 id="web-interface">Web Interface</h3>

<p>The web interface is secured with an OAuth login from GitHub.  There is a whitelist
of allowed GitHub users that can access the interface.</p>

<p>The flow for web clients connecting with Socket.IO is much easier since they are already authenticated
with OAuth from GitHub.</p>

<ol>
  <li>The user authenticates with GitHub</li>
  <li>The Socket.IO connection includes cookies such as the session, which is a
signed by a secret key on the server.  The session’s github key is compared to the
whitelist of allowed users.</li>
</ol>

<h2 id="storage-of-tests-and-results">Storage of tests and results</h2>

<p>Storage of the tests and results are still being designed.  Most likely, the
tests and results will be stored in a database such as Postgres.</p>

<h1 id="conclusions">Conclusions</h1>

<p><a href="https://heroku.com">Heroku</a> provides a great playing ground to prototype these
web applications. I hope that I can find an alternative eventually that will run on
OSG’s production kubernetes installation.</p>

<p>The web application is still be developed, and there is much to be done before
it can be fully utilized for the scale validation.  But, many of the difficult
components are completed, including the communcation and eventing, secure web
interface, and clients.</p>

<p>The GitHub repos are available at:</p>

<ul>
  <li><a href="https://github.com/djw8605/xrootd-client-manager">XRootD Client Manager</a></li>
  <li><a href="https://github.com/djw8605/xrootd-ws-client">XRootD Client</a></li>
</ul></li>

<li><a href="https://derekweitzel.com/2020/03/08/gracc-transition/">GRACC Transition Visualization</a><br/><p>The OSG is in the progress of transitioning from an older ElasticSearch (ES) cluster to a new version.  Part of this process is reindexing (copying) data from the old to the new.  Unfortunately, it’s not easy to capture a status of this transition.  For this, I have created the <a href="https://gracc-transition.herokuapp.com/">GRACC Transition page</a>.</p>

<p>The goal is to transition when both the old and new ES have the same data.  A simple measure of this is if they share the same number of documents in all of the indexes.</p>

<p>Source for this app is available on github: <a href="https://github.com/djw8605/gracc-transition">GRACC Transition</a></p>

<h2 id="data-collection">Data Collection</h2>

<p>Data collection is performed by a probe on each the new and old ElasticSearch clusters.  Upload is performed with a POST to the gracc transition website.  Authorization is performed with a shared random token between the probe and the website.</p>

<p>The probe is very simple.  It queries ES for all indexes, as well as the number of documents and data size inside the index.</p>

<p>There are also many indexes that the OSG is not transitioning to the new ES.  In order to ignore these indexes, a set of regular expressions is used to remove the indexes from consideration.  Those regular expressions are:</p>

<div class="language-plaintext highlighter-rouge"><div class="highlight"><pre class="highlight"><code>/^osg.*/,           // Start with osg.*
/^ps_.*/,           // Start with ps_*
/^shrink\-ps_.*/,   // Start with shrink-ps_*
/^glidein.*/,       // Start with glidein*
/^\..*/,            // Start with .
/^ps\-itb.*/        // Start with ps-itb*
</code></pre></div></div>

<h2 id="the-website">The Website</h2>

<p><img alt="GRACC Transition Website" src="https://derekweitzel.com/images/posts/gracc-transition/gracc-transition-website.png" /></p>

<p>The gracc transition app is hosted on the <a href="https://www.heroku.com/">Heroku</a>.  I choose Heroku because it provides a simple hosting platform with a database for free.</p>

<p>The website pushes alot of the data processing to the client.  The data is stored in the database as JSON and is sent to the client without any transformation.  The client pulls the data from the website for both the new and old ES and begins to process the data within javascript.</p>

<p>The website breaks the statistics into three visualizations:</p>

<ol>
  <li><strong>Progress Bars</strong>: Comparing the total documents and total data size of the old and new.  The progress is defined as new / old.  The bars provide a very good visualization of the progress of the transition as they need to reach 100% before we are able to fully transition.</li>
  <li><strong>Summary Statistics</strong>: The summary statistics show the raw number of either missing or mismatched indexes.  If an index is in the old ES but is not in the new ES, it is counted as <strong>missing</strong>.  If the index is a different size in the old vs. the new, it is counted as <strong>mismatched</strong>.</li>
  <li><strong>Table of Indices</strong>: Finally, a table of indices is shown with the number of documents that are missing, or simply <strong>Missing</strong> if the index is missing in the new ES.</li>
</ol>

<p>In addition to the table, I also provide a button to download the list of indexes that are missing or mismatched.  This can be useful for an administrator to make sure it matches what they expect or to process with elasticsearch.</p>

<h2 id="improvements-and-future">Improvements and Future</h2>

<p>In the future, I would like to generate a weekly or even daily email to show the progress of the transition.  This would give provide a constant reminder of the state of the transition.</p></li>

</ul>
