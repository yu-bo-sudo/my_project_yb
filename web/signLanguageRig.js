/**
 * 骨骼运动控制器
 * 提取自 three-mediapipe-rig 的核心运动逻辑
 * 不依赖摄像头，通过参数输入控制骨骼运动
 */

import * as THREE from 'three';

// ==================== 核心算法 ====================

/**
 * lookAt 算法 - 让骨骼朝向目标点，同时保持极轴方向
 * @param object 要旋转的对象
 * @param target 目标点（世界坐标）
 * @param poleTarget 极轴目标点（世界坐标）
 * @param poleAxis 极轴方向
 */
export function lookAt(
    object: THREE.Object3D,
    target: THREE.Vector3,
    poleTarget: THREE.Vector3,
    poleAxis: '+x' | '-x' | '+y' | '-y' = '+x'
) {
    const XAxis = new THREE.Vector3(1, 0, 0);
    const XAxisNeg = new THREE.Vector3(-1, 0, 0);
    const YAxis = new THREE.Vector3(0, 1, 0);
    const YAxisNeg = new THREE.Vector3(0, -1, 0);
    const ZAxis = new THREE.Vector3(0, 0, 1);

    const poleDir = new THREE.Vector3();
    const objectPosition = new THREE.Vector3();
    const pole = new THREE.Vector3();
    const lookDir = new THREE.Vector3();
    const v = new THREE.Vector3();
    const correction = new THREE.Quaternion();
    const worldQuat = new THREE.Quaternion();

    // 让对象朝向目标
    object.lookAt(target);

    const axis = poleAxis === '+x' ? XAxis :
                 poleAxis === '-x' ? XAxisNeg :
                 poleAxis === '+y' ? YAxis : YAxisNeg;

    object.getWorldPosition(objectPosition);
    object.getWorldQuaternion(worldQuat);

    poleDir.subVectors(poleTarget, objectPosition).normalize();

    // 当前极轴方向（世界空间）
    pole.copy(axis).applyQuaternion(worldQuat);
    const currentPole = pole;

    // 看向方向（世界空间）
    const lookAxisDir = lookDir.copy(ZAxis).applyQuaternion(worldQuat);

    // 将期望的极轴方向投影到垂直于看向轴的平面上
    const desiredPoleDir = poleDir.clone().addScaledVector(lookAxisDir, -poleDir.dot(lookAxisDir)).normalize();

    // 计算当前极轴和期望极轴之间的有符号角度
    const cross = v.crossVectors(currentPole, desiredPoleDir);
    const angle = Math.atan2(cross.dot(lookAxisDir), currentPole.dot(desiredPoleDir));

    // 应用修正旋转
    correction.setFromAxisAngle(ZAxis, angle);
    object.quaternion.multiply(correction);
}

// ==================== 手指运动控制器 ====================

/**
 * 手指骨骼运动控制器
 * 根据弯曲程度计算手指骨骼的旋转
 */
export class FingerRigController {
    private ghost: THREE.Object3D;
    private v1 = new THREE.Vector3();
    private v2 = new THREE.Vector3();
    private v3 = new THREE.Vector3();
    private v4 = new THREE.Vector3();

    constructor() {
        this.ghost = new THREE.Object3D();
    }

    /**
     * 设置手指弯曲
     * @param bones 手指骨骼数组 [掌指关节, 近端关节, 远端关节]
     * @param curlAmount 弯曲程度 0-1
     * @param axis 弯曲轴
     * @param direction 弯曲方向 1 或 -1
     */
    setFingerCurl(
        bones: THREE.Bone[],
        curlAmount: number,
        axis: 'x' | 'y' | 'z' = 'x',
        direction: 1 | -1 = 1
    ) {
        const HALF_PI = Math.PI / 2;

        for (let i = 0; i < bones.length; i++) {
            const bone = bones[i];
            if (!bone) continue;

            // 弯曲角度：近端关节弯曲更多，远端递减
            const jointFactor = 1 - (i * 0.2);
            const angle = curlAmount * HALF_PI * jointFactor * direction;

            // 设置旋转
            bone.rotation[axis] = angle;
        }
    }

    /**
     * 使用方向向量设置骨骼旋转（更精确的方法）
     * @param bone 骨骼
     * @param direction 目标方向（世界空间）
     * @param poleDirection 极轴方向（世界空间）
     * @param poleAxis 极轴
     */
    setBoneDirection(
        bone: THREE.Bone,
        direction: THREE.Vector3,
        poleDirection: THREE.Vector3,
        poleAxis: '+x' | '-x' | '+y' | '-y' = '+x'
    ) {
        const bonePos = bone.getWorldPosition(this.v1);
        const targetPos = this.v2.copy(bonePos).add(direction);
        const polePos = this.v3.copy(bonePos).add(poleDirection);

        lookAt(this.ghost, targetPos, polePos, poleAxis);
        this.ghost.rotateX(Math.PI / 2);

        // 将 ghost 的旋转应用到骨骼
        bone.quaternion.copy(this.ghost.quaternion);
    }
}

// ==================== 手臂运动控制器 ====================

/**
 * 手臂骨骼运动控制器
 */
export class ArmRigController {
    private ghost: THREE.Object3D;
    private v1 = new THREE.Vector3();
    private v2 = new THREE.Vector3();

    constructor() {
        this.ghost = new THREE.Object3D();
    }

    /**
     * 设置手臂关节旋转
     * @param bone 骨骼
     * @param rotation 旋转角度 {x, y, z} 弧度
     */
    setArmRotation(bone: THREE.Bone, rotation: { x: number; y: number; z: number }) {
        bone.rotation.x = rotation.x;
        bone.rotation.y = rotation.y;
        bone.rotation.z = rotation.z;
    }

    /**
     * 平滑过渡到目标旋转
     * @param bone 骨骼
     * @param targetRotation 目标旋转
     * @param delta 时间增量
     * @param speed 过渡速度
     */
    lerpRotation(
        bone: THREE.Bone,
        targetRotation: { x: number; y: number; z: number },
        delta: number,
        speed: number = 5
    ) {
        bone.rotation.x += (targetRotation.x - bone.rotation.x) * delta * speed;
        bone.rotation.y += (targetRotation.y - bone.rotation.y) * delta * speed;
        bone.rotation.z += (targetRotation.z - bone.rotation.z) * delta * speed;
    }
}

// ==================== 完整的手语控制器 ====================

/**
 * 手语动作控制器
 * 整合手指和手臂控制
 */
export class SignLanguageController {
    private fingerController: FingerRigController;
    private armController: ArmRigController;
    private bones: Map<string, THREE.Bone> = new Map();

    constructor() {
        this.fingerController = new FingerRigController();
        this.armController = new ArmRigController();
    }

    /**
     * 注册骨骼
     */
    registerBone(name: string, bone: THREE.Bone) {
        this.bones.set(name, bone);
    }

    /**
     * 从模型自动注册所有骨骼
     */
    registerBonesFromModel(model: THREE.Object3D) {
        model.traverse((child) => {
            if ((child as THREE.Bone).isBone) {
                this.bones.set(child.name, child as THREE.Bone);
            }
        });
    }

    /**
     * 获取骨骼
     */
    getBone(name: string): THREE.Bone | undefined {
        return this.bones.get(name);
    }

    /**
     * 设置手指弯曲
     * @param fingerNames 手指骨骼名称数组
     * @param curl 弯曲程度 0-1
     * @param axis 弯曲轴
     * @param direction 弯曲方向
     */
    setFingerCurl(
        fingerNames: string[],
        curl: number,
        axis: 'x' | 'y' | 'z' = 'x',
        direction: 1 | -1 = 1
    ) {
        const bones = fingerNames
            .map(name => this.bones.get(name))
            .filter(b => b !== undefined) as THREE.Bone[];

        this.fingerController.setFingerCurl(bones, curl, axis, direction);
    }

    /**
     * 设置手臂旋转
     */
    setArmRotation(boneName: string, rotation: { x: number; y: number; z: number }) {
        const bone = this.bones.get(boneName);
        if (bone) {
            this.armController.setArmRotation(bone, rotation);
        }
    }

    /**
     * 应用手语姿势
     */
    applyPose(pose: {
        fingers?: {
            [finger: string]: {
                bones: string[];
                curl: number;
                axis?: 'x' | 'y' | 'z';
                direction?: 1 | -1;
            };
        };
        arm?: {
            [joint: string]: {
                bone: string;
                rotation: { x: number; y: number; z: number };
            };
        };
    }) {
        // 应用手指姿势
        if (pose.fingers) {
            for (const [fingerName, fingerData] of Object.entries(pose.fingers)) {
                this.setFingerCurl(
                    fingerData.bones,
                    fingerData.curl,
                    fingerData.axis || 'x',
                    fingerData.direction || 1
                );
            }
        }

        // 应用手臂姿势
        if (pose.arm) {
            for (const [jointName, jointData] of Object.entries(pose.arm)) {
                this.setArmRotation(jointData.bone, jointData.rotation);
            }
        }
    }
}

export default SignLanguageController;
