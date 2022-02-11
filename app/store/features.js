export const state = () => ({
    data: [],
    response: null,
    dynamicPath: '',
})

export const mutations = {
    payload(state, payload) {
        state.data = payload
    },
    setResponse(state, payload) {
        state.response = payload
    },
    setDynamicPath(state, payload) {
        state.dynamicPath = payload
    }
}

export const actions = {
    async deleteCard(context) {
        const path = `/card/query/delete/${context.getters.getDynamicPath}`;
        return this.$axios.delete(path)
            .then((res) => {
                context.commit('setResponse', res.data)
            })
            .catch((err) => {
                context.commit('setResponse', err)
                this.$notifier.showMessage({
                    content: `มีบางอย่างผิดพลาด status code ${err.response.status}`,
                    color: 'red'
                })
            })

    },
}


export const getters = {
    getPayload(state) {
        return state.data
    },
    getResponse(state) {
        return state.response
    },
    getDynamicPath(state) {
        return state.dynamicPath
    }
}