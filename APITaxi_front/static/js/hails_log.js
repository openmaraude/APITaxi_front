<hailslog>
    <h1>Hails POST and PUT</h1>
    <div id="error">{error}</div>
    <ul>
    <li each={hails_states}>
        <h4>Method: {method} @ {datetime}</h4><br/>
        <h5>Initial status: {initial_status}</h5>
        <div>
          <a data-toggle="collapse" href="#collapsePayload"
              aria-expanded="false" aria-controls="collapsePayload">
                Payload
          </a>
          <div class="collapse" id="collapsePayload">
              <div class="card card-block">
                {payload}
              </div>
          </div>
        </div>
        <h5>Return code: {code}</h5>

        <div>
          <a data-toggle="collapse" href="#collapseReturn"
              aria-expanded="false" aria-controls="collapseReturn">
                Return
          </a>
          <div class="collapse" id="collapseReturn">
              <div class="card card-block">
                {payload}
              </div>
          </div>
        </div>
    </li>
    </ul>
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
                this.hails_states = r.data.map(function(state){
                    var d = new Date(state['datetime']);
                    state['datetime'] = d.toISOString();
                    return state;
                });
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
</hailslog>
