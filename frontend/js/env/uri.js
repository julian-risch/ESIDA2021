const URI = {
    history_cnt: 0,

    __parse_state: () => {
        let params = window.location.hash.substr(1);
        return new URLSearchParams(params);
    },
    __store_state: (params) => {
        window.location.hash = '#' + params.toString();
    },
    set_val: (key, value, reload = false) => {
        let state = URI.__parse_state();
        if (Array.isArray(value)) {
            state.delete(key);
            value.forEach((val) => state.append(key, val));
        } else state.set(key, value);
        URI.__store_state(state);
        if (reload)
            location.reload();
    },
    __get_val: (key) => {
        let state = URI.__parse_state();
        return state.get(key);
    },
    get_str: (key, def_value) => {
        let val = URI.__get_val(key);
        if (val === null) return def_value;
        return val;
    },
    get_arr: (key, def_value) => {
        let state = URI.__parse_state();
        let value = state.getAll(key);
        console.log(value)
        if (value === null || value.length < 1) return def_value;
        console.log('def_value not returned')
        return value.map((val) => isNaN(val) ? val : parseInt(val));
    },
    get_int: (key, def_value) => {
        let val = URI.__get_val(key);
        if (val === null) return def_value;
        return parseInt(val);
    },
    get_bool: (key, def_value) => {
        let val = URI.__get_val(key);
        if (val === null) return def_value;
        return val === 'true';
    },
    del: (key) => {
        let state = URI.__parse_state();
        state.delete(key);
        URI.__store_state(state);
    }
}

export { URI };