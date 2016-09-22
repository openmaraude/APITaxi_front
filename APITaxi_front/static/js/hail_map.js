<json>
<code></code>
try {
    this.root.innerHTML = library.json.prettyPrint(opts.content)
} catch(e) {
    this.root.innerHTML = opts.content;
}
</json>
<hailmap>
            <div><h3>Distance : {dist_}</h3></div>
            <div><h3>Adresse envoyée par le client : {address}</h3></div>
            <div><h3>Adresse reverse géocodée du client : {reverse}</h3></div>
            <div><br/></div>
            <div><h2>Status</h2></div>
            <div>
                <ul>
                    <li each={state, i in hails_states}>
                        <h4>Method: {state.method} @ {state.datetime}</h4><br/>
                        <h5>Initial status: {state.initial_status}</h5>
                    </li>
                </ul>
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
                   var customer_coords = [r['customer_lat'], r['customer_lon']];
                   var taxi_coords = [r['taxi']['lat'], r['taxi']['lon']];
                   var m1 = L.marker(customer_coords, {icon: customerMarker})
                       .addTo(map)
                       .bindTooltip("Adresse: "+this.address);
                   var m2 = L.marker(taxi_coords, {icon: carMarker}).addTo(map);
                   var line = L.polyline([customer_coords, taxi_coords], {color: 'grey'})
                       .addTo(map).bindTooltip("Distance: "+this.dist_, {permanent:true});
                   var group = new L.featureGroup([m1, m2]);
                   map.fitBounds(group.getBounds());
                   var url_reverse = 'http://api-adresse.data.gouv.fr/reverse/?lat='+
                                      customer_coords[0]+'&lon='+customer_coords[1];

                   fetch(url_reverse)
                       .then(function(response2){
                            const status = response2 ? response2.status : 500;
                            if (status === 200) {
                                return response2.json();
                            }
                            throw response2;
                       })
                       .then(function(r2){
                            this.reverse = r2['features'][0]['properties']['label'];
                            this.update();
                       }.bind(this));
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
