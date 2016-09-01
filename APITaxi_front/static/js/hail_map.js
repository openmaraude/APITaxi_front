<json>
<code></code>
try {
    this.root.innerHTML = library.json.prettyPrint(opts.content)
} catch(e) {
    this.root.innerHTML = opts.content;
}
</json>
<hailmap>
    <h1>Hails  and PUT</h1>
    <div style="float: left;">
    <div>
        <div id="map"></div>
        <div><h3>Distance : {dist_}</h3></div>
        <div><h3>Adresse du client : {address}</h3></div>
    </div>
    <div>
        <div id="error">{error}</div>
        <ul>
        <li each={state, i in hails_states}>
            <h4>Method: {state.method} @ {state.datetime}</h4><br/>
            <h5>Initial status: {state.initial_status}</h5>
        </li>
        </ul>
    </div>
    </div>
    this.hails_states = [];
    this.error = '';
    load() {
        var headers = {"Accept": "application/json",
                       "X-VERSION": 2,
                       "X-API-KEY": opts.apikey
        };
        fetch('/hails/' + opts.hail_id + '/_log', {headers:headers})
            .then(function(response) {
                const status = response ? response.status : 500;
                if (status === 200) {
                    return response.json();
                }
                throw response;
            })
            .then(function(r) {
                this.error = "";
                this.post_state = null;
                this.hails_states = r.data.map(function(state){
                    var d = new Date(state['datetime'] * 1000);
                    state['datetime'] = d.toISOString();
                    if (state['method'] == 'POST') {
                        this.post_state = state;
                    }
                    return state;
                });
                if (post_state != null) {
                   r = JSON.parse(post_state.return)['data'][0];
                   this.dist_ = distance(r['customer_lon'], r['customer_lat'],
                                        r['taxi']['lon'], r['taxi']['lat'], 'K');
                   this.address = r['customer_address'];
                   var customerMarker = L.AwesomeMarkers.icon({
                       icon: 'hand-spock-o',
                       markerColor: 'red',
                       prefix: 'fa'
                   });
                   var carMarker = L.AwesomeMarkers.icon({
                       icon: 'taxi',
                       markerColor: 'blue',
                       prefix: 'fa'
                   });
                   var m1 = L.marker([r['customer_lat'], r['customer_lon']],
                            {icon: customerMarker}).addTo(map);
                   var m2 = L.marker([r['taxi']['lat'], r['taxi']['lon']],
                            {icon: carMarker}).addTo(map);
                   var group = new L.featureGroup([m1, m2]);
                   map.fitBounds(group.getBounds());
                }
                if (this.hails_states.length == 0) {
                    this.error = "No log for this hail";
                }
                this.update();
            }.bind(this)).catch(function(response){
                const status = response ? response.status : 500;
                if (status === 404) {
                    this.error = "Unable to find hail";
                } else if (status === 403) {
                    this.error = "You're not allowed to see this hail";
                } else {
                    this.error = "Unknown error: "+ response
                }
                this.update();
            }.bind(this));
    }
    this.load();
</hailmap>
