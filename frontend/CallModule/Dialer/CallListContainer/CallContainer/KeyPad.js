import React from "react";
import { Button, Image, View, Text } from "react-native";
import EndConferenceButton from "./EndConferenceButton";
import backspace from "../assets/images/backspace.svg";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class KeyPad extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      pressedKey: ""
    };
  }

  sendDtmfTone = (e) => {
    const { innerHTML: textContent } = e.currentTarget.firstChild;
    const { currentConnection } = this.props;
    const { pressedKey } = this.state;
    this.setState(
      { ...this.state, pressedKey: `${pressedKey}${textContent}` },
      () => currentConnection.sendDigits(textContent)
    );
  };

  clearKeys = () => {
    const { pressedKey } = this.state;
    const xtractedPressedKey = pressedKey.split("");
    xtractedPressedKey.pop();
    this.setState({
      ...this.state,
      pressedKey: `${xtractedPressedKey.join("")}`
    });
  };

  onKeyDownEvent = async (e) => {
    const { key } = e;
    const regexAllowedChars = /^[\d\(\)\+\*\#\-\ ]+$/;
    if (key.toLowerCase() === "backspace") {
      this.clearKeys();
      return true;
    }
    if (regexAllowedChars.test(key)) {
      this.sendDtmfTone({ currentTarget: { textContent: key } });
    }
  };

  render() {
    const {
      toggleKeypad,
      callElement,
      currentConnection,
      user,
      shouldDisableButton,
      alterButtonDiableProperty
    } = this.props;
    const { pressedKey } = this.state;
    return (
      <View
        className="keypadfullsec"
        onKeyDown={this.onKeyDownEvent}
        tabIndex={-1}
      >
        <View className="keypadnumberinputbox">
          <Text
            name="keyNumber"
            id="keyNumber"
            disabled
            value={pressedKey}
          ></Text>
          {pressedKey !== "" && (
            <Button
              className="removecolorbut backspace"
              onPress={() => this.clearKeys()}
              disabled={shouldDisableButton}
            >
              <Image source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${backspace}`} />
            </Button>
          )}
        </View>
        <View className="grid-container">
          <View className="grid-item" onClick={(e) => this.sendDtmfTone(e)}>
            <Text>1</Text>
          </View>
          <View className="grid-item" onClick={(e) => this.sendDtmfTone(e)}>
            <Text>2</Text>
            <Text>A B C</Text>
          </View>
          <View className="grid-item" onClick={(e) => this.sendDtmfTone(e)}>
            <Text>3</Text>
            <Text>D E F</Text>
          </View>
          <View className="grid-item" onClick={(e) => this.sendDtmfTone(e)}>
            <Text>4</Text>
            <Text>G H I</Text>
          </View>
          <View className="grid-item" onClick={(e) => this.sendDtmfTone(e)}>
            <Text>5</Text>
            <Text>J K L</Text>
          </View>
          <View className="grid-item" onClick={(e) => this.sendDtmfTone(e)}>
            <Text>6</Text>
            <Text>M N O</Text>
          </View>
          <View className="grid-item" onClick={(e) => this.sendDtmfTone(e)}>
            <Text>7</Text>
            <Text>P Q R S</Text>
          </View>
          <View className="grid-item" onClick={(e) => this.sendDtmfTone(e)}>
            <Text>8</Text>
            <Text>T U V</Text>
          </View>
          <View className="grid-item" onClick={(e) => this.sendDtmfTone(e)}>
            <Text>9</Text>
            <Text>W X Y Z</Text>
          </View>
          <View className="grid-item" onClick={(e) => this.sendDtmfTone(e)}>
            <Text>*</Text>
          </View>
          <View className="grid-item" onClick={(e) => this.sendDtmfTone(e)}>
            <Text>0</Text>
            <Text>+</Text>
          </View>
          <View className="grid-item" onClick={(e) => this.sendDtmfTone(e)}>
            <Text>#</Text>
          </View>
        </View>
        <View className="keypadendcallsec">
          <EndConferenceButton
            callElement={callElement}
            currentConnection={currentConnection}
            user={user}
            conferenaceSid={callElement.conference.sid}
            shouldDisableButton={shouldDisableButton}
            alterButtonDiableProperty={alterButtonDiableProperty}
          />
          <Button
            className="removecolorbut hideicon"
            onPress={() => toggleKeypad()}
            value="Hide"
          >
          </Button>
        </View>
      </View>
    );
  }
}

export default KeyPad;
