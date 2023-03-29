import React from "react";
import { Button, View, Image, Text, TextInput, ScrollView,StyleSheet } from "react-native";
import moment from "moment";
import { fancyTimeFormat } from "../CallListContainer/assets/library/helper";
import searchicon from "../CallListContainer/assets/images/searchicon.svg";
import smallcallicon from "../CallListContainer/assets/images/smallcallicon.svg";
import smallmessageicon from "../CallListContainer/assets/images/smallmessageicon.svg";
import inbound from "./assets/images/inbound.svg";
import outbound from "./assets/images/outbound.svg";
import missed from "./assets/images/missedcall.svg";
import voicemail from "./assets/images/voicemail.svg";
import playbutton from "./assets/images/calllogplayicon.svg";
import pause from "../CallListContainer/assets/images/stopicon.svg";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;
import Icon from "react-native-vector-icons/FontAwesome5";

class CallLogs extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      allLogs: [],
      isPlaying: false,
      audio: null,
      audioElementIndex: "",
      filteredCallLogs: [],
      audioDuration: null,
      audioCurrentTime: null,
    };
  }

  componentDidMount() {
    const { callLogDetails } = this.props;
    this.setState({
      ...this.state,
      allLogs: callLogDetails,
      filteredCallLogs: callLogDetails,
    });
  }

  componentWillUnmount() {
    const { allLogs } = this.state;
    const { markCallLogAsRead } = this.props;
    markCallLogAsRead(allLogs);
  }

  shouldComponentUpdate(nextprops) {
    if (nextprops.callLogDetails.length !== this.state.allLogs.length) {
      this.setState({
        ...this.state,
        allLogs: nextprops.callLogDetails,
        filteredCallLogs: nextprops.callLogDetails,
      });
    }

    nextprops.callLogDetails.map((element, index) => {
      if (
        this.state.allLogs[index] &&
        this.state.allLogs[index].forwarding !== element.forwarding
      ) {
        this.setState({
          ...this.state,
          allLogs: [...nextprops.callLogDetails],
          filteredCallLogs: [...nextprops.callLogDetails],
        });
      }
    });
    return true;
  }

  getContactDetails = (logElement) => {
    const contactUserDetails = { name: "", number: "" };
    if (logElement.direction === "inbound") {
      contactUserDetails.name = logElement.source.name;
      contactUserDetails.number = logElement.source.number;
    } else {
      contactUserDetails.name = logElement.destination.name;
      contactUserDetails.number = logElement.destination.number;
    }
    return contactUserDetails;
  };

  getCallIcon = (logElement) => {
    if (logElement.direction === "outbound-api") {
      return outbound;
    } else {
      if (logElement.callStatus === "completed") {
        return inbound;
      } else {
        if (
          logElement.forwarding !== null &&
          logElement.forwarding.voicemail !== null &&
          logElement.forwarding.voicemail.url !== null
        ) {
          return voicemail;
        }
        return missed;
      }
    }
  };

  playAudio = (playBackAudioUrl, elementIndex) => {
    const { alterButtonDiableProperty } = this.props;
    const { audioElementIndex, audio, isPlaying } = this.state;
    if (isPlaying) {
      audio.pause();
      this.setState(
        {
          ...this.state,
          audioElementIndex: null,
          audio: null,
          isPlaying: false,
          audioCurrentTime: null,
          audioDuration: null,
        },
        () => alterButtonDiableProperty(false)
      );
    }

    if (audioElementIndex !== elementIndex) {
      this.setState(
        {
          ...this.state,
          audio: new Audio(playBackAudioUrl),
          audioElementIndex: elementIndex,
        },
        () => {
          this.state.audio.onloadedmetadata = () => {
            this.state.audio.play();
            this.setState({
              ...this.state,
              isPlaying: true,
              audioDuration:
                Math.floor(this.state.audio.duration / 60) +
                ":" +
                ("0" + Math.floor(this.state.audio.duration % 60)).slice(-2),
            });
          };
          this.state.audio.onended = () => {
            this.setState(
              {
                ...this.state,
                isPlaying: false,
                audio: null,
                audioElementIndex: "",
                audioCurrentTime: null,
                audioDuration: null,
              },
              () => alterButtonDiableProperty(false)
            );
          };

          this.state.audio.addEventListener(
            "timeupdate",
            (event) => {
              const currentTime =
                Math.floor(this.state.audio.currentTime / 60) +
                ":" +
                ("0" + Math.floor(this.state.audio.currentTime % 60)).slice(-2);
              this.setState({ ...this.state, audioCurrentTime: currentTime });
            },
            false
          );
        }
      );
    }
  };

  filterContact = (e) => {
    const { value } = e.target;
    const { allLogs } = this.state;
    let filteredConversation = [...allLogs];
    if (value !== "") {
      filteredConversation = allLogs.filter((callElement) => {
        if (callElement.source.name === null) {
          callElement.source.name = callElement.source.number;
        }
        if (callElement.destination.name === null) {
          callElement.destination.name = callElement.destination.number;
        }
        return (
          callElement.source.name.toLowerCase().includes(value) ||
          callElement.source.number.toLowerCase().includes(value) ||
          callElement.destination.name.toLowerCase().includes(value) ||
          callElement.destination.number.toLowerCase().includes(value)
        );
      });
    }
    this.setState({
      ...this.state,
      filteredCallLogs: [...filteredConversation],
    });
  };

  render() {
    const {
      filteredCallLogs,
      isPlaying,
      audio,
      audioElementIndex,
      audioCurrentTime,
      audioDuration,
    } = this.state;
    const {
      handleDialer,
      alterButtonDiableProperty,
      shouldDisableButton,
      activeCallCount,
      syncCallLogconnectionProps,
      numbersInCalls,
    } = this.props;
    return (
      <View style={{ flex: 1, flexDirection: "row" }} >
        <View>
          {/* <View className="popupboxclose" onClick={() => handleDialer()}>
            <Text>&#x00d7;</Text>
          </View>
          <View className="contactuslist">
            <Text>Call History</Text>
          </View> */}
        </View>
        <View className="searchboxsec">
          <TextInput
            type="text"
            name="contactSearchInput"
            id="contactSearchInput"
            placeholder="Search Call Logs"
            onChange={(e) => this.filterContact(e)}
          />
        </View>
        <ScrollView>
          <View className="phonebooklist phonebooklist callloglistsec">
            {syncCallLogconnectionProps.status !== "connected" && (
              <View className="errorMessage">
                {syncCallLogconnectionProps.message}
              </View>
            )}
            {filteredCallLogs.length > 0 &&
              [...filteredCallLogs].reverse().map((logElement, index) => {
                return (
                  <View
                    className={`phonebookbox ${!logElement.isRead && "isRead"}`}
                    key={index}
                  >
                    <View className="firsttext">
                      <View className="Nameletters">
                        <Image
                          style={{
                            margin: 0,
                          }}
                          source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${this.getCallIcon(
                            logElement
                          )}`}
                        />
                      </View>
                    </View>
                    <View className="phonebooknum">
                      <Text
                        data-bs-toggle="tooltip"
                        data-bs-placement="bottom"
                        title={this.getContactDetails(logElement).name}
                      >
                        {this.getContactDetails(logElement).name}
                        {/* <span className="phonebooklead">Lead</span> */}
                      </Text>
                      <Text>{this.getContactDetails(logElement).number}</Text>

                      <Text>
                        {moment
                          .utc(logElement.timestamp)
                          .local()
                          .format("MMM DD YYYY h:mm A")}
                        {logElement.duration > 0 && (
                          <Text>
                            &nbsp;|&nbsp;{fancyTimeFormat(logElement.duration)}{" "}
                          </Text>
                        )}
                      </Text>
                      {logElement.callStatus === "missed" &&
                        logElement.forwarding !== null && (
                          <View className="forwardcalllist">
                            {logElement.forwarding.from !== "null" && (
                              <Text>
                                Forwarded from&nbsp;
                                {logElement.forwarding.from.name}
                              </Text>
                            )}
                            {logElement.forwarding.to !== "null" && (
                              <Text>
                                Forwarded to&nbsp;{" "}
                                {logElement.forwarding.to.name}
                              </Text>
                            )}

                            {logElement.forwarding.answewredBy !== "null" && (
                              <Text>
                                Answered by &nbsp;
                                {logElement.forwarding.answewredBy.name}
                              </Text>
                            )}

                            {logElement.forwarding.voicemail !== "null" && (
                              <Text>
                                Voicemail sent to&nbsp;
                                {logElement.forwarding.voicemail.name}
                              </Text>
                            )}
                          </View>
                        )}
                    </View>

                    <View className="phonebookicon">
                      {logElement.forwarding !== null &&
                        logElement.forwarding.voicemail !== null &&
                        logElement.forwarding.voicemail.url !== null && (
                          <View className="voicemailiconsec">
                            <Icon
                              name={
                                isPlaying &&
                                logElement.callSId === audioElementIndex
                                  ? "pause"
                                  : "play"
                              }
                              id={logElement.callSId}
                              disabled={
                                shouldDisableButton &&
                                audio !== null &&
                                isPlaying &&
                                logElement.callSId !== audioElementIndex
                              }
                            />
                            <Text className="voicemailaudioduration">
                              {audio !== null &&
                                audioElementIndex === logElement.callSId &&
                                isPlaying &&
                                `${audioCurrentTime} / ${audioDuration}`}
                            </Text>
                          </View>
                        )}
                      <Icon
                        name={"envelope"}
                        id={logElement.callSId}
                        onClick={(e) => {
                          alterButtonDiableProperty(true);
                          window.startCreateatingConversation(
                            this.getContactDetails(logElement).number,
                            this.getContactDetails(logElement),
                            true
                          );
                        }}
                        disabled={isPlaying || shouldDisableButton}
                      />

                      <Icon
                        name={"phone"}
                        id={logElement.callSId}
                        onClick={(e) => {
                          alterButtonDiableProperty(true);
                          window.makeOutBoundCall(
                            this.getContactDetails(logElement).number,
                            this.getContactDetails(logElement).name
                          );
                        }}
                        disabled={
                          isPlaying ||
                          shouldDisableButton ||
                          activeCallCount > 0 ||
                          numbersInCalls.includes(
                            this.getContactDetails(logElement).number
                          )
                        }
                      ></Icon>
                    </View>
                  </View>
                );
              })}
            {filteredCallLogs.length === 0 && (
              <View className="noresult">
                <Text>No results found</Text>
              </View>
            )}
          </View>
        </ScrollView>
      </View>
    );
  }
}

export default CallLogs;
