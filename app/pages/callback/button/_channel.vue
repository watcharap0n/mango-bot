<template>
  <div>

    <v-card flat>
      <v-toolbar
          color="info"
          dense
          dark
          flat
      >
        <v-icon>mdi-reply</v-icon>&nbsp;
        <v-toolbar-title>Quick Reply</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn color="white"
               @click="dialog = true"
               :hidden="!btnShow"
               text
        >
          <v-icon left>mdi-reply</v-icon>
          Add Quick Reply
        </v-btn>

      </v-toolbar>
      <v-row
          class="pa-4"
          justify="space-between"
      >
        <v-col cols="12" sm="4">
          <v-treeview
              dense
              :active.sync="active"
              :items="items"
              :load-children="fetchItems"
              :open.sync="open"
              activatable
              color="info"
              open-on-click
              transition
          >
            <template v-slot:prepend="{ item }">
              <div v-if="!item.children && selected">
                <v-icon v-if="item.id === selected.id" color="red">
                  mdi-reply
                </v-icon>
                <v-icon v-else color="red">
                  mdi-reply-outline
                </v-icon>
              </div>
            </template>

            <template v-slot:label="{item}">
              <div>{{ item.name }}</div>
            </template>

          </v-treeview>
        </v-col>

        <v-col
            cols="12" sm="8"
        >
          <v-scroll-y-transition mode="out-in">
            <div
                v-if="!selected"
                class="text-h6 grey--text text--lighten-1 font-weight-light"
                style="align-self: center;"
            >
              select item
            </div>
            <v-card
                v-else
                :key="selected.id"
                flat
            >
              <v-card-text>

                <QuickReply
                    :button="selected"
                    :users.sync="users"
                    :intent="intent"
                >
                </QuickReply>

              </v-card-text>

            </v-card>
          </v-scroll-y-transition>
        </v-col>
      </v-row>
    </v-card>

    <Dialog :dialog.sync="dialog"
            header="Add Quick Reply"
            :element-forms="elements"
            max-width="450"
            body="Please set your name Quick Reply!"
            :loading-dialog="!spinSave"
            :submit-dialog="save"
    />

  </div>
</template>

<script>
import Dialog from "@/components/app/Dialog";
import QuickReply from "@/components/callback/QuickReply";


export default {
  components: {Dialog, QuickReply},
  data() {
    return {
      intent: [],
      dialog: false,
      dialogDelete: false,
      spinSave: true,
      btnShow: false,
      setName: '',
      form: {
        name: '',
        access_token: '',
        intent: "",
        texts: [],
        labels: [],
        reply: []
      },
      defaultForm: {
        name: '',
        access_token: '',
        intent: "",
        texts: [],
        labels: [],
        reply: []
      },
      data: [],
      active: [],
      avatar: null,
      open: [],
      users: [],
      elements: [
        {
          color: 'primary',
          label: 'Name Quick reply',
          rules: [v => !!v || 'required'],
          icon: 'mdi-reply',
          value: this.setName
        }
      ]
    }
  },
  computed: {
    items() {
      return [
        {
          name: 'My Quick Reply',
          children: this.users,
        },
      ]
    },
    selected() {
      if (!this.active.length) return undefined
      const id = this.active[0]
      return this.users.find(user => user.id === id)
    },
  },
  async created() {
    await this.$parent.$emit('routerHandle', this.$route.params);
  },
  methods: {
    async fetchItems(item) {
      if (this.item) return

      await this.fetchToken()
      let encoded = encodeURIComponent(this.form.access_token);
      const path = `/button/?access_token=${encoded}`;
      await this.$axios.get(path)
          .then((res) => {
            res.data.forEach((v) => {
              v.id = v._id
            })
            item.children.push(...res.data);
            this.getIntent(encoded)
          })
          .catch((err) => {
            console.error(err);
          })
      this.btnShow = true;
    },
    async fetchToken() {
      const path = `/callback/channel/info/${this.$route.params.channel}`;
      await this.$axios.get(path)
          .then((res) => {
            this.form.access_token = res.data.access_token
          })
          .catch((err) => {
            this.$notifier.showMessage({
              content: `something wrong ${err.response.status}`,
              color: 'red'
            })
            console.error(err);
          })
    },
    async save() {
      this.spinSave = false
      await this.fetchToken()
      this.form.name = this.elements[0].value
      const path = '/button/create'
      this.$axios.post(path, this.form)
          .then((res) => {
            this.form = res.data
            this.form.id = this.form._id
            this.users.push(this.form)
            this.form = Object.assign({}, this.defaultForm)
            this.$notifier.showMessage({
              content: 'created quick reply successfully',
              color: 'success'
            })
          })
          .catch((err) => {
            console.error(err)
            if (err.response.status === 400) {
              this.$notifier.showMessage({
                content: `duplicate name quick reply  ${this.form.name}`,
                color: 'red'
              })
            } else {
              this.$notifier.showMessage({
                content: `something wrong! ${err.response.status}`,
                color: 'red'
              })
            }
          })
      this.dialog = false;
      this.spinSave = true
      this.elements[0].value = ''
    },
    async getIntent(accessToken) {
      const path = `/intents/?access_token=${accessToken}`
      this.$store.commit('features/setDynamicPath', path)
      await this.$store.dispatch('features/fetchCard')
      this.intent = this.$store.getters["features/getResponse"]
    }
  },

}
</script>

<style scoped>
</style>