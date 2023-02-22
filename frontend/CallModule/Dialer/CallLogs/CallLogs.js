import React from "react";
import { Button, View, Image, Text } from "react-native";
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
      audioCurrentTime: null
    };
  }

  componentDidMount() {
    const { callLogDetails } = this.props;
    this.setState({
      ...this.state,
      allLogs: callLogDetails,
      filteredCallLogs: callLogDetails
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
        filteredCallLogs: nextprops.callLogDetails
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
          filteredCallLogs: [...nextprops.callLogDetails]
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
          audioDuration: null
        },
        () => alterButtonDiableProperty(false)
      );
    }

    if (audioElementIndex !== elementIndex) {
      this.setState(
        {
          ...this.state,
          audio: new Audio(playBackAudioUrl),
          audioElementIndex: elementIndex
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
                ("0" + Math.floor(this.state.audio.duration % 60)).slice(-2)
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
                audioDuration: null
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
      filteredCallLogs: [...filteredConversation]
    });
  };

  render() {
    const {
      filteredCallLogs,
      isPlaying,
      audio,
      audioElementIndex,
      audioCurrentTime,
      audioDuration
    } = this.state;
    const {
      handleDialer,
      alterButtonDiableProperty,
      shouldDisableButton,
      activeCallCount,
      syncCallLogconnectionProps,
      numbersInCalls
    } = this.props;
    return (
      <View className="secondaryParticipant">
        <View className="mainboxheader">
          <View className="popupboxclose" onClick={() => handleDialer()}>
            <span>&#x00d7;</span>
          </View>
          <View className="contactuslist">
            <h4>Call History</h4>
          </View>
        </View>
        <View className="searchboxsec">
          <input
            type="text"
            name="contactSearchInput"
            id="contactSearchInput"
            placeholder="Search Call Logs"
            onChange={(e) => this.filterContact(e)}
          />
          <Image
            source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${searchicon}`}
          />
        </View>
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
                          margin: "0"
                        }}
                        source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${this.getCallIcon(
                          logElement
                        )}`}
                      />
                    </View>
                  </View>
                  <View className="phonebooknum">
                    <span
                      data-bs-toggle="tooltip"
                      data-bs-placement="bottom"
                      title={this.getContactDetails(logElement).name}
                    >
                      {this.getContactDetails(logElement).name}
                      {/* <span className="phonebooklead">Lead</span> */}
                    </span>
                    <span>{this.getContactDetails(logElement).number}</span>

                    <p>
                      {moment
                        .utc(logElement.timestamp)
                        .local()
                        .format("MMM DD YYYY h:mm A")}
                      {logElement.duration > 0 && (
                        <span>
                          &nbsp;|&nbsp;{fancyTimeFormat(logElement.duration)}{" "}
                        </span>
                      )}
                    </p>
                    {logElement.callStatus === "missed" &&
                      logElement.forwarding !== null && (
                        <View className="forwardcalllist">
                          {logElement.forwarding.from !== "null" && (
                            <p>
                              Forwarded from&nbsp;
                              {logElement.forwarding.from.name}
                            </p>
                          )}
                          {logElement.forwarding.to !== "null" && (
                            <p>
                              Forwarded to&nbsp; {logElement.forwarding.to.name}
                            </p>
                          )}

                          {logElement.forwarding.answewredBy !== "null" && (
                            <p>
                              Answered by &nbsp;
                              {logElement.forwarding.answewredBy.name}
                            </p>
                          )}

                          {logElement.forwarding.voicemail !== "null" && (
                            <p>
                              Voicemail sent to&nbsp;
                              {logElement.forwarding.voicemail.name}
                            </p>
                          )}
                        </View>
                      )}
                  </View>

                  <View className="phonebookicon">
                    {logElement.forwarding !== null &&
                      logElement.forwarding.voicemail !== null && 
                      logElement.forwarding.voicemail.url !== null && (
                        <View className="voicemailiconsec">
                          <Button
                            id={logElement.callSId}
                            className="removecolorbut pauseplayicon smallcallicon"
                            onClick={(e) => {
                              alterButtonDiableProperty(true);
                              this.playAudio(
                                logElement.forwarding.voicemail.url,
                                logElement.callSId
                              );
                            }}
                            disabled={
                              shouldDisableButton &&
                              audio !== null &&
                              isPlaying &&
                              logElement.callSId !== audioElementIndex
                            }
                          >
                            <Image
                              source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${
                                isPlaying &&
                                logElement.callSId === audioElementIndex
                                  ? pause
                                  : playbutton
                              }`}
                            />
                          </Button>
                          <span className="voicemailaudioduration">
                            {audio !== null &&
                              audioElementIndex === logElement.callSId &&
                              isPlaying &&
                              `${audioCurrentTime} / ${audioDuration}`}
                          </span>
                        </View>
                      )}
                    <Button
                      id={logElement.callSId}
                      className="removecolorbut smallcallicon"
                      onClick={(e) => {
                        alterButtonDiableProperty(true);
                        window.startCreateatingConversation(
                          this.getContactDetails(logElement).number,
                          this.getContactDetails(logElement),
                          true
                        );
                      }}
                      disabled={isPlaying || shouldDisableButton}
                    >
                      <Image
                        source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${smallmessageicon}`}
                      />
                    </Button>

                    <Button
                      id={logElement.callSId}
                      className="removecolorbut smallcallicon"
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
                    >
                      <Image
                        source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${smallcallicon}`}
                      />
                    </Button>
                  </View>
                </View>
              );
            })}
          {filteredCallLogs.length === 0 && (
            <View className="noresult">No results found</View>
          )}
        </View>
      </View>
    );
  }
}

export default CallLogs;
