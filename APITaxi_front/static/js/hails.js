<hails>
    <table class="hails pure-table">
    <thead>
    <tr>
        <td>Id</td>
        <td>Creation</td>
        <td>Added by</td>
        <td>Operator</td>
        <td>Current status</td>
    </tr>
    </thead>
    <tbody>
        <tr each={hails}>
            <td>{id}</td>
            <td>{creation_datetime}</td>
            <td>{added_by}</td>
            <td>{operateur}</td>
            <td>{status}</td>
        </tr>
    </tbody>
    </table>
    this.hails = [];
    load(apikey) {
        var headers = {"Accept": "application/json",
                       "X-VERSION": 2,
                       "X-API-KEY": opts.apikey
        };
        fetch('/hails/', {headers:headers})
            .then(function(response) {
                return response.json();
            })
            .then(function(r) {
                this.hails = r.data;
                this.update();
            }.bind(this), console.error.bind(console));
    }
    this.load();
</hails>

